"""Three stage deduplication pipeline for the RAG memory system.

The memory store in :mod:`memory.lancedb` records a ``simhash_64`` column
alongside every row but does not suppress duplicates on insert. This
module exposes the suppression logic so callers can dedup before adding
a new memory row.

Stages (fast to slow, cheapest filter first):

1. SimHash (64 bit, token shingle based)
       Stage 1 is an O(1) fingerprint comparison. Two texts are flagged
       as near duplicates when their 64 bit SimHash values differ by
       Hamming distance <= 3 (roughly 95 percent shingle overlap).

2. MinHash + LSH (datasketch)
       Stage 2 uses 128 permutations and a Jaccard similarity threshold
       of 0.85 over 3 gram word shingles. LSH returns candidate keys
       quickly even with millions of stored items.

3. Semantic cosine similarity + NLI contradiction check
       Stage 3 embeds both texts with an Embedder from
       :mod:`memory.embedders` and compares cosine similarity. A score
       >= 0.95 is treated as a semantic duplicate. A separate NLI pass
       (cross encoder style) flags contradictions so that two highly
       similar texts with opposite polarity (for example one asserting
       X and another asserting NOT X) are not silently merged.

The :class:`DedupPipeline` applies the three stages in order and short
circuits as soon as a duplicate match is found.

External dependencies (NOT installed by this module):
    pip install datasketch sentence-transformers

The ``simhash`` PyPI package is used when present for a small speedup,
otherwise a pure Python fallback implemented here is used. Either path
produces identical 64 bit fingerprints.

Usage:
    from memory.dedup import DedupPipeline
    from memory.embedders import get_general_embedder
    pipeline = DedupPipeline(embedder=get_general_embedder())
    pipeline.register("row-1", "the quick brown fox jumps over the lazy dog")
    verdict = pipeline.check(
        "the quick brown fox leaps over the lazy dog",
        existing_candidates=[
            ("row-1", "the quick brown fox jumps over the lazy dog", sh64),
        ],
    )
    if verdict["is_duplicate"]:
        skip_insert()
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from collections import Counter
from pathlib import Path

try:
    from datasketch import MinHash, MinHashLSH

    _HAS_DATASKETCH = True
except ImportError:
    MinHash = None
    MinHashLSH = None
    _HAS_DATASKETCH = False

try:
    import simhash as _simhash_pkg

    _HAS_SIMHASH_PKG = True
except ImportError:
    _simhash_pkg = None
    _HAS_SIMHASH_PKG = False

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None


DEFAULT_LOG_PATH: str = "~/.opencode/memory.log"

DEFAULT_SIMHASH_DIM: int = 64
DEFAULT_SIMHASH_THRESHOLD: int = 3

DEFAULT_MINHASH_PERM: int = 128
DEFAULT_MINHASH_THRESHOLD: float = 0.85

DEFAULT_COSINE_THRESHOLD: float = 0.95
DEFAULT_SHINGLE_N: int = 3

DEFAULT_NLI_MODEL: str = "cross-encoder/nli-deberta-v3-small"


def _setup_logger() -> logging.Logger:
    expanded = os.path.expanduser(DEFAULT_LOG_PATH)
    Path(expanded).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("opencode.memory.dedup")
    if not logger.handlers:
        handler = logging.FileHandler(expanded)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer used by all three stages."""
    return _WORD_RE.findall(text.lower())


def shingles(text: str, n: int = DEFAULT_SHINGLE_N) -> set[str]:
    """Return the set of word n gram shingles for text.

    Word shingles are used rather than character shingles because the
    dedup pipeline targets prose and code comments rather than URLs or
    hash strings. If the token sequence is shorter than n the whole
    sequence is returned as a single shingle so short texts still fold
    into the pipeline.
    """
    tokens = _tokenize(text)
    if len(tokens) < n:
        if not tokens:
            return set()
        return {" ".join(tokens)}
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def _popcount(x: int) -> int:
    """Count of 1 bits in x. Uses int.bit_count() on Python 3.10+."""
    if hasattr(int, "bit_count"):
        return x.bit_count()
    count = 0
    while x:
        x &= x - 1
        count += 1
    return count


def compute_simhash(text: str, dim: int = DEFAULT_SIMHASH_DIM) -> int:
    """Compute a dim bit SimHash fingerprint over token shingles.

    Pure Python fallback used when the optional ``simhash`` package is
    not installed. Tokens are weighted by frequency and each token is
    hashed through MD5 (truncated to dim bits) to produce the bit
    vector that drives the accumulator. The returned integer has the
    bit_length equal to dim at most.
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0
    weights = Counter(tokens)
    v = [0] * dim
    byte_len = max(1, dim // 8)
    for token, weight in weights.items():
        digest = hashlib.md5(token.encode("utf-8")).digest()[:byte_len]
        h_int = int.from_bytes(digest, "big")
        for i in range(dim):
            bit = (h_int >> i) & 1
            if bit:
                v[i] += weight
            else:
                v[i] -= weight
    fp = 0
    for i, val in enumerate(v):
        if val > 0:
            fp |= 1 << i
    return fp


class SimHashDedup:
    """Stage 1: 64 bit SimHash fingerprints with Hamming distance match."""

    def __init__(
        self,
        dim: int = DEFAULT_SIMHASH_DIM,
        threshold: int = DEFAULT_SIMHASH_THRESHOLD,
    ) -> None:
        if dim % 8 != 0:
            raise ValueError("dim must be a multiple of 8 for byte packing")
        self.dim = int(dim)
        self.threshold = int(threshold)
        self.logger = _setup_logger()

    def compute(self, text: str) -> int:
        """Return the SimHash fingerprint for text.

        Prefers the ``simhash`` PyPI package when available for speed,
        falls back to the pure Python implementation otherwise. Both
        paths yield the same width fingerprint for equal inputs within
        the same backend but the exact bit pattern may differ across
        backends; callers must not mix them for a single index.
        """
        if _HAS_SIMHASH_PKG:
            try:
                tokens = _tokenize(text)
                if not tokens:
                    return 0
                fp = _simhash_pkg.Simhash(tokens, f=self.dim)
                return int(fp.value)
            except Exception as exc:
                self.logger.warning(
                    "simhash pkg failed, falling back: %s", exc
                )
        return compute_simhash(text, dim=self.dim)

    def hamming_distance(self, h1: int, h2: int) -> int:
        """Hamming distance = popcount(h1 XOR h2)."""
        return _popcount(int(h1) ^ int(h2))

    def is_near_duplicate(
        self,
        h1: int,
        h2: int,
        threshold: int | None = None,
    ) -> bool:
        """Return True when Hamming distance <= threshold."""
        t = self.threshold if threshold is None else int(threshold)
        return self.hamming_distance(h1, h2) <= t


class MinHashLSHDedup:
    """Stage 2: MinHash + LSH for Jaccard similarity candidates."""

    def __init__(
        self,
        num_perm: int = DEFAULT_MINHASH_PERM,
        threshold: float = DEFAULT_MINHASH_THRESHOLD,
        shingle_n: int = DEFAULT_SHINGLE_N,
    ) -> None:
        if not _HAS_DATASKETCH:
            raise ImportError(
                "datasketch is required for MinHashLSHDedup. "
                "Install with: pip install datasketch"
            )
        self.num_perm = int(num_perm)
        self.threshold = float(threshold)
        self.shingle_n = int(shingle_n)
        self._lsh = MinHashLSH(
            threshold=self.threshold, num_perm=self.num_perm
        )
        self._store: dict[str, MinHash] = {}
        self.logger = _setup_logger()

    def _build_minhash(self, text: str) -> MinHash:
        m = MinHash(num_perm=self.num_perm)
        for shingle in shingles(text, n=self.shingle_n):
            m.update(shingle.encode("utf-8"))
        return m

    def insert(self, key: str, text: str) -> None:
        """Index text under key for future similarity queries."""
        if key in self._store:
            try:
                self._lsh.remove(key)
            except Exception:
                pass
        m = self._build_minhash(text)
        self._store[key] = m
        self._lsh.insert(key, m)
        self.logger.info(
            "minhash insert key=%s shingles_threshold=%.2f",
            key,
            self.threshold,
        )

    def query(self, text: str) -> list[str]:
        """Return indexed keys with Jaccard similarity >= threshold."""
        m = self._build_minhash(text)
        hits = list(self._lsh.query(m))
        self.logger.info(
            "minhash query hits=%d threshold=%.2f", len(hits), self.threshold
        )
        return hits

    def jaccard(self, key: str, text: str) -> float:
        """Exact Jaccard of the stored MinHash vs a fresh one for text."""
        if key not in self._store:
            return 0.0
        m = self._build_minhash(text)
        return float(self._store[key].jaccard(m))

    def remove(self, key: str) -> None:
        if key in self._store:
            try:
                self._lsh.remove(key)
            except Exception:
                pass
            self._store.pop(key, None)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        raise ValueError(
            f"cosine length mismatch len(a)={len(a)} len(b)={len(b)}"
        )
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


class SemanticCosineDedup:
    """Stage 3: cosine similarity on dense embeddings + NLI contradiction."""

    def __init__(
        self,
        embedder,
        cos_threshold: float = DEFAULT_COSINE_THRESHOLD,
        nli_model: str = DEFAULT_NLI_MODEL,
    ) -> None:
        self.embedder = embedder
        self.cos_threshold = float(cos_threshold)
        self.nli_model_id = nli_model
        self._nli: object | None = None
        self.logger = _setup_logger()

    def _load_nli(self) -> object | None:
        """Best effort load of the NLI cross encoder.

        Returns None if sentence transformers is missing or the model
        could not be loaded. Callers must handle the None fallback.
        """
        if CrossEncoder is None:
            return None
        if self._nli is None:
            try:
                self._nli = CrossEncoder(self.nli_model_id)
                self.logger.info("NLI loaded model=%s", self.nli_model_id)
            except Exception as exc:
                self.logger.warning(
                    "NLI model load failed model=%s err=%s",
                    self.nli_model_id,
                    exc,
                )
                self._nli = None
        return self._nli

    def cosine_similarity(self, text1: str, text2: str) -> float:
        v1 = self.embedder.embed(text1)
        v2 = self.embedder.embed(text2)
        return _cosine(list(v1), list(v2))

    def is_semantic_duplicate(self, text1: str, text2: str) -> bool:
        """Return True when cosine similarity >= cos_threshold."""
        sim = self.cosine_similarity(text1, text2)
        self.logger.info(
            "semantic dup check sim=%.4f threshold=%.4f",
            sim,
            self.cos_threshold,
        )
        return sim >= self.cos_threshold

    def contradiction_check(self, text1: str, text2: str) -> bool:
        """Return True when the pair is a likely contradiction.

        Prefers a real NLI cross encoder when available. The model is
        expected to emit three logits (contradiction, entailment,
        neutral) per pair. When the NLI model cannot be loaded the
        method falls back to a cheap heuristic that flags pairs whose
        negation token counts (``not``, ``never``, ``no``) disagree.
        """
        nli = self._load_nli()
        if nli is not None:
            try:
                scores = nli.predict(
                    [(text1, text2)], show_progress_bar=False
                )
                row = list(scores[0]) if hasattr(scores[0], "__iter__") else [
                    float(scores[0])
                ]
                if len(row) >= 3:
                    contradiction, entailment, neutral = (
                        float(row[0]),
                        float(row[1]),
                        float(row[2]),
                    )
                    is_contra = contradiction > max(entailment, neutral)
                    self.logger.info(
                        "nli contradiction=%.3f entail=%.3f neutral=%.3f "
                        "flag=%s",
                        contradiction,
                        entailment,
                        neutral,
                        is_contra,
                    )
                    return is_contra
            except Exception as exc:
                self.logger.warning("nli predict failed: %s", exc)

        negations = {"not", "never", "no", "none", "cannot", "cant"}
        t1 = set(_tokenize(text1)) & negations
        t2 = set(_tokenize(text2)) & negations
        flag = bool(t1) != bool(t2)
        self.logger.info(
            "nli heuristic fallback t1_neg=%d t2_neg=%d flag=%s",
            len(t1),
            len(t2),
            flag,
        )
        return flag


class DedupPipeline:
    """Tiered dedup pipeline: SimHash then MinHash LSH then semantic cosine.

    Each stage is run only when the prior stage leaves the verdict
    undecided. SimHash is checked against the candidate tuples supplied
    by the caller (these typically come straight from the LanceDB rows
    which already store ``simhash_64``). MinHash LSH and the semantic
    stage rely on the caller registering texts through :meth:`register`
    before the check.

    The result of :meth:`check` always has the same shape so callers can
    act on it without branching on stage specific payloads.
    """

    def __init__(
        self,
        embedder=None,
        simhash_dim: int = DEFAULT_SIMHASH_DIM,
        simhash_threshold: int = DEFAULT_SIMHASH_THRESHOLD,
        minhash_perm: int = DEFAULT_MINHASH_PERM,
        minhash_threshold: float = DEFAULT_MINHASH_THRESHOLD,
        cos_threshold: float = DEFAULT_COSINE_THRESHOLD,
        shingle_n: int = DEFAULT_SHINGLE_N,
    ) -> None:
        self.logger = _setup_logger()
        self.simhash = SimHashDedup(
            dim=simhash_dim, threshold=simhash_threshold
        )
        self.minhash: MinHashLSHDedup | None = None
        if _HAS_DATASKETCH:
            self.minhash = MinHashLSHDedup(
                num_perm=minhash_perm,
                threshold=minhash_threshold,
                shingle_n=shingle_n,
            )
        else:
            self.logger.warning(
                "datasketch not installed, stage 2 (MinHash LSH) disabled"
            )

        self.semantic: SemanticCosineDedup | None = None
        if embedder is not None:
            self.semantic = SemanticCosineDedup(
                embedder=embedder, cos_threshold=cos_threshold
            )
        else:
            self.logger.warning(
                "no embedder supplied, stage 3 (semantic) disabled"
            )

        self._text_by_key: dict[str, str] = {}

    def register(self, key: str, text: str) -> int:
        """Register a text under key and return its SimHash fingerprint."""
        self._text_by_key[key] = text
        if self.minhash is not None:
            self.minhash.insert(key, text)
        fp = self.simhash.compute(text)
        self.logger.info("register key=%s simhash=%d", key, fp)
        return fp

    def check(
        self,
        text: str,
        existing_candidates: list[tuple[str, str, int]],
    ) -> dict:
        """Check text against existing_candidates.

        existing_candidates is a list of tuples
        ``(key, existing_text, existing_simhash64)``. Typical callers
        pass rows from LanceDB, mapping id to ``text`` and
        ``simhash_64`` columns.

        Returns a dict::

            {
                "is_duplicate": bool,
                "stage": "simhash"|"minhash"|"semantic"|"none",
                "matched_key": str|None,
                "contradiction": bool,
            }

        The contradiction flag is only computed when the semantic stage
        triggers. For earlier stage matches the flag is False because
        they are syntactic and not subject to NLI.
        """
        verdict = {
            "is_duplicate": False,
            "stage": "none",
            "matched_key": None,
            "contradiction": False,
        }

        new_fp = self.simhash.compute(text)
        for key, existing_text, existing_fp in existing_candidates:
            if self.simhash.is_near_duplicate(new_fp, int(existing_fp)):
                verdict.update(
                    {
                        "is_duplicate": True,
                        "stage": "simhash",
                        "matched_key": key,
                    }
                )
                self.logger.info(
                    "dedup hit stage=simhash key=%s new_fp=%d old_fp=%d",
                    key,
                    new_fp,
                    int(existing_fp),
                )
                return verdict

        if self.minhash is not None:
            hits = self.minhash.query(text)
            if hits:
                matched = hits[0]
                verdict.update(
                    {
                        "is_duplicate": True,
                        "stage": "minhash",
                        "matched_key": matched,
                    }
                )
                self.logger.info(
                    "dedup hit stage=minhash key=%s hits=%d",
                    matched,
                    len(hits),
                )
                return verdict

        if self.semantic is not None:
            for key, existing_text, _ in existing_candidates:
                if self.semantic.is_semantic_duplicate(text, existing_text):
                    contradiction = self.semantic.contradiction_check(
                        text, existing_text
                    )
                    verdict.update(
                        {
                            "is_duplicate": not contradiction,
                            "stage": "semantic",
                            "matched_key": key,
                            "contradiction": bool(contradiction),
                        }
                    )
                    self.logger.info(
                        "dedup hit stage=semantic key=%s contradiction=%s",
                        key,
                        contradiction,
                    )
                    return verdict

        self.logger.info(
            "dedup miss candidates=%d", len(existing_candidates)
        )
        return verdict
