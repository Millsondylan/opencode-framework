"""Embedding model wrappers for the opencode-framework RAG memory system.

Two specialised encoders are exposed:

* General text encoder:
    model_id  : Qwen/Qwen3-Embedding-0.6B
    dim       : 1024
    format    : documented 4-bit DWQ quantization target (actual bitsandbytes
                quantization is optional for this reference implementation;
                the wrapper runs full precision by default and only emits a
                log line noting the target format).

* Code encoder:
    preferred : jinaai/jina-code-embeddings-0.5B (repo id as listed in spec)
    fallback  : jinaai/jina-embeddings-v2-base-code
                jinaai/jina-embeddings-v2-small-code
    dim       : reported by the loaded model. The spec targets 512; if the
                loaded model reports a different dim, that value is used and
                the runtime dim is exposed via CodeEmbedder.dim.
    format    : documented 4-bit quantization target (same reference caveat).

Both wrappers lazy load their underlying SentenceTransformer on first use.
Module level singletons are exposed via get_general_embedder() and
get_code_embedder() to keep a single copy resident while honouring the 2 GB
RAM cap enforced by memory.lancedb.

External dependencies (NOT installed by this module):
    pip install sentence-transformers

Optional runtime accelerators:
    torch with MPS (Apple Silicon) or CUDA (NVIDIA) will be detected and a
    warning emitted so the caller can pick a non cpu device explicitly.

Usage:
    from memory.embedders import route, embed_both, get_general_embedder
    g = route("plain english query", is_code=False)
    c = route("def foo():\\n    return 1", is_code=True)
    pair = embed_both("hybrid query text")
"""

from __future__ import annotations

import logging
import os
import warnings
from abc import ABC, abstractmethod
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError as exc:
    raise ImportError(
        "sentence-transformers is required for memory.embedders. "
        "Install with: pip install sentence-transformers"
    ) from exc


GENERAL_MODEL_ID: str = "Qwen/Qwen3-Embedding-0.6B"
CODE_MODEL_CANDIDATES: tuple[str, ...] = (
    "jinaai/jina-code-embeddings-0.5B",
    "jinaai/jina-embeddings-v2-base-code",
    "jinaai/jina-embeddings-v2-small-code",
)

GENERAL_DIM: int = 1024
CODE_DIM_TARGET: int = 512

DEFAULT_LOG_PATH: str = "~/.opencode/memory.log"


def _setup_logger() -> logging.Logger:
    expanded = os.path.expanduser(DEFAULT_LOG_PATH)
    Path(expanded).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("opencode.memory.embedders")
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
                "CUDA detected. Pass device='cuda' to embedder ctors for speed.",
                stacklevel=2,
            )
            return "cuda"
        mps_ok = getattr(torch.backends, "mps", None) is not None and (
            torch.backends.mps.is_available()
        )
        if mps_ok:
            warnings.warn(
                "Apple MPS detected. Pass device='mps' to embedder ctors "
                "for Apple Silicon acceleration.",
                stacklevel=2,
            )
            return "mps"
    except Exception:
        return "cpu"
    return "cpu"


class Embedder(ABC):
    """Abstract base for single vector text embedders."""

    model_id: str = ""
    dim: int = 0

    def __init__(self, device: str | None = None) -> None:
        self.device = device or _detect_device()
        self._model: SentenceTransformer | None = None
        self.logger = _setup_logger()

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            self.logger.info(
                "loading model=%s device=%s", self.model_id, self.device
            )
            self._model = SentenceTransformer(self.model_id, device=self.device)
            reported = getattr(
                self._model, "get_sentence_embedding_dimension", lambda: 0
            )()
            if reported and reported != self.dim:
                self.logger.info(
                    "model %s reported dim=%d target=%d, using %d",
                    self.model_id,
                    reported,
                    self.dim,
                    reported,
                )
                self.dim = int(reported)
        return self._model

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return a single embedding vector for the given text."""


class GeneralEmbedder(Embedder):
    """Qwen3-Embedding-0.6B wrapper (target: 4-bit DWQ quantization, dim 1024)."""

    model_id = GENERAL_MODEL_ID
    dim = GENERAL_DIM

    def embed(self, text: str) -> list[float]:
        model = self._load()
        vec = model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        out = [float(x) for x in list(vec)]
        if len(out) != self.dim:
            self.logger.warning(
                "general embed dim mismatch expected=%d got=%d",
                self.dim,
                len(out),
            )
        return out


class CodeEmbedder(Embedder):
    """jina code embeddings wrapper (target: 4-bit quantization)."""

    model_id = CODE_MODEL_CANDIDATES[0]
    dim = CODE_DIM_TARGET

    def _load(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        last_err: Exception | None = None
        for candidate in CODE_MODEL_CANDIDATES:
            try:
                self.logger.info(
                    "loading code model candidate=%s device=%s",
                    candidate,
                    self.device,
                )
                self._model = SentenceTransformer(candidate, device=self.device)
                self.model_id = candidate
                reported = getattr(
                    self._model,
                    "get_sentence_embedding_dimension",
                    lambda: 0,
                )()
                if reported:
                    if reported != self.dim:
                        self.logger.info(
                            "code model %s dim=%d (target was %d)",
                            candidate,
                            reported,
                            self.dim,
                        )
                    self.dim = int(reported)
                return self._model
            except Exception as load_exc:
                last_err = load_exc
                self.logger.warning(
                    "code model %s failed: %s", candidate, load_exc
                )
                continue
        raise RuntimeError(
            f"No jina code embedding model could be loaded. "
            f"Tried: {CODE_MODEL_CANDIDATES}. Last error: {last_err}"
        )

    def embed(self, text: str) -> list[float]:
        model = self._load()
        vec = model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [float(x) for x in list(vec)]


_general: GeneralEmbedder | None = None
_code: CodeEmbedder | None = None


def get_general_embedder() -> GeneralEmbedder:
    """Return a module wide GeneralEmbedder singleton."""
    global _general
    if _general is None:
        _general = GeneralEmbedder()
    return _general


def get_code_embedder() -> CodeEmbedder:
    """Return a module wide CodeEmbedder singleton."""
    global _code
    if _code is None:
        _code = CodeEmbedder()
    return _code


def route(text: str, is_code: bool) -> list[float]:
    """Dispatch to the appropriate embedder based on the is_code flag."""
    if is_code:
        return get_code_embedder().embed(text)
    return get_general_embedder().embed(text)


def embed_both(text: str) -> dict[str, list[float]]:
    """Return both the general and code embeddings for a single text.

    The general embedding always runs. The code embedding runs against the
    same input text so the caller can store both columns for any row.
    """
    return {
        "general": get_general_embedder().embed(text),
        "code": get_code_embedder().embed(text),
    }
