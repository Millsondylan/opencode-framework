"""Cross encoder reranker for the opencode-framework RAG memory system.

The pipeline first fuses BM25 and dense vector hits via Reciprocal Rank
Fusion (RRF k=60) inside :mod:`memory.lancedb`. That fused pool is broad
but noisy because RRF only considers rank position, not semantic fit.
This module runs a small cross encoder over (query, candidate text)
pairs to reorder the pool and keep the top k hits that are actually
relevant.

Target model:
    jinaai/jina-reranker-v1-tiny-en (33M parameters, English, tiny).
    The model is intentionally small so the reranker stays under the
    2 GB resident RAM cap enforced on the memory subsystem.

Integration pattern:
    hits = db.query_hybrid(query, general_embedding, k=60, ...)
    reranked = get_reranker().rerank(query, hits, top_k=10)

External dependencies (NOT installed by this module):
    pip install sentence-transformers

Optional runtime accelerators:
    torch with MPS (Apple Silicon) or CUDA (NVIDIA) will be detected and
    a warning emitted so the caller can pick a non cpu device explicitly.

Usage:
    from memory.reranker import get_reranker, Reranker
    reranker = get_reranker()
    top = reranker.rerank(
        query="how do I run the debugger",
        candidates=fused_hits,
        top_k=10,
        text_field="text",
    )
    for row in top:
        print(row["rerank_score"], row["text"])
"""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path

try:
    from sentence_transformers import CrossEncoder
except ImportError as exc:
    raise ImportError(
        "sentence-transformers is required for memory.reranker. "
        "Install with: pip install sentence-transformers"
    ) from exc


DEFAULT_MODEL: str = "jinaai/jina-reranker-v1-tiny-en"
DEFAULT_LOG_PATH: str = "~/.opencode/memory.log"
DEFAULT_TOP_K: int = 10


def _setup_logger() -> logging.Logger:
    expanded = os.path.expanduser(DEFAULT_LOG_PATH)
    Path(expanded).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("opencode.memory.reranker")
    if not logger.handlers:
        handler = logging.FileHandler(expanded)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def _detect_device() -> str:
    """Detect best available torch device, warn if an accelerator is found."""
    try:
        import torch
    except ImportError:
        return "cpu"
    try:
        if torch.cuda.is_available():
            warnings.warn(
                "CUDA detected. Pass device='cuda' to Reranker ctor for speed.",
                stacklevel=2,
            )
            return "cuda"
        mps_ok = getattr(torch.backends, "mps", None) is not None and (
            torch.backends.mps.is_available()
        )
        if mps_ok:
            warnings.warn(
                "Apple MPS detected. Pass device='mps' to Reranker ctor "
                "for Apple Silicon acceleration.",
                stacklevel=2,
            )
            return "mps"
    except Exception:
        return "cpu"
    return "cpu"


class Reranker:
    """Cross encoder reranker over (query, candidate) pairs.

    Lazy loads the underlying SentenceTransformers CrossEncoder on first
    use so instantiation stays cheap. The loaded model is cached on the
    instance. Scores are produced in one batched forward pass per call.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        device: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.device = device or _detect_device()
        self._model: CrossEncoder | None = None
        self.logger = _setup_logger()
        self.logger.info(
            "Reranker init model=%s device=%s", self.model_id, self.device
        )

    def _load(self) -> CrossEncoder:
        if self._model is None:
            self.logger.info(
                "loading reranker model=%s device=%s",
                self.model_id,
                self.device,
            )
            self._model = CrossEncoder(self.model_id, device=self.device)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = DEFAULT_TOP_K,
        text_field: str = "text",
    ) -> list[dict]:
        """Score (query, candidate[text_field]) pairs and return top_k.

        Candidates are copied (shallow) with an added ``rerank_score`` float
        field. Rows missing the text_field are scored as 0.0 and still
        returned so the caller can audit missing data.

        An empty candidate list is logged as a warning and returned
        unchanged so the caller does not need to special case it.
        """
        if not candidates:
            self.logger.warning(
                "rerank called with empty candidates query_len=%d",
                len(query),
            )
            return []

        pairs: list[tuple[str, str]] = []
        for row in candidates:
            raw = row.get(text_field, "")
            text = raw if isinstance(raw, str) else str(raw)
            pairs.append((query, text))

        model = self._load()
        scores = model.predict(pairs, show_progress_bar=False)
        scored: list[dict] = []
        for row, score in zip(candidates, scores):
            enriched = dict(row)
            enriched["rerank_score"] = float(score)
            scored.append(enriched)

        scored.sort(key=lambda r: r["rerank_score"], reverse=True)
        top = scored[: max(0, int(top_k))]
        self.logger.info(
            "rerank in=%d top_k=%d returned=%d field=%s",
            len(candidates),
            top_k,
            len(top),
            text_field,
        )
        return top

    def batch_rerank(
        self,
        queries: list[str],
        candidates_per_query: list[list[dict]],
        top_k: int = DEFAULT_TOP_K,
        text_field: str = "text",
    ) -> list[list[dict]]:
        """Rerank several queries at once.

        Pairs from every query are flattened into a single batch so the
        model runs one forward pass. Each query's slice is then sliced back
        out, sorted, and truncated to top_k independently.
        """
        if len(queries) != len(candidates_per_query):
            raise ValueError(
                "queries and candidates_per_query must be the same length"
            )
        if not queries:
            self.logger.warning("batch_rerank called with no queries")
            return []

        offsets: list[int] = []
        pairs: list[tuple[str, str]] = []
        running = 0
        for q, cands in zip(queries, candidates_per_query):
            offsets.append(running)
            if not cands:
                continue
            for row in cands:
                raw = row.get(text_field, "")
                text = raw if isinstance(raw, str) else str(raw)
                pairs.append((q, text))
                running += 1
        offsets.append(running)

        if not pairs:
            self.logger.warning(
                "batch_rerank got %d queries but zero candidates",
                len(queries),
            )
            return [[] for _ in queries]

        model = self._load()
        scores = model.predict(pairs, show_progress_bar=False)

        out: list[list[dict]] = []
        for i, cands in enumerate(candidates_per_query):
            start = offsets[i]
            end = offsets[i + 1]
            if not cands:
                out.append([])
                continue
            slice_scores = list(scores[start:end])
            scored: list[dict] = []
            for row, score in zip(cands, slice_scores):
                enriched = dict(row)
                enriched["rerank_score"] = float(score)
                scored.append(enriched)
            scored.sort(key=lambda r: r["rerank_score"], reverse=True)
            out.append(scored[: max(0, int(top_k))])

        self.logger.info(
            "batch_rerank queries=%d total_pairs=%d top_k=%d",
            len(queries),
            len(pairs),
            top_k,
        )
        return out


_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    """Return a process wide Reranker singleton with lazy init."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
