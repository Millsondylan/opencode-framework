"""Memory consolidation pipeline for the opencode-framework RAG system.

This module composes the low level memory building blocks (LanceDB store,
dense embedders, cross encoder reranker, three stage dedup pipeline) into
a single ``Consolidator`` surface that agents can drive with three verbs:

* ``consolidate_new(text, namespace, ttl_tier, metadata)``
    Fingerprint, embed, dedup check against the nearest 20 existing rows,
    merge by bumping access count on a hit, or insert a fresh row on a
    miss. Contradictions detected by the semantic stage of the dedup
    pipeline are recorded in telemetry but never silently merged; they
    still insert the new row so callers can inspect both sides.

* ``recall(query, namespace_priority, top_k)``
    Hybrid BM25 plus dense retrieval (RRF at k=60) from LanceDB followed
    by a cross encoder rerank over the top 20 fused hits. Namespace
    priority multipliers (session=1.0, project=0.7, global=0.4) are
    applied to the rerank score before the final top_k cut.

* ``consolidate_background(batch_size)``
    Per row composite staleness pass using the Park 2023 formula
    (relevance plus exponential time decay plus access frequency). Rows
    whose staleness crosses 0.9 are deleted and the drop count is logged
    so a daemon can track consolidation behaviour.

Park 2023 composite staleness (used by :class:`StalenessScorer`):

    staleness =
        w_sim  * (1 - similarity_to_query)
      + w_time * (1 - exp(-lambda_time * age_seconds))
      + w_freq * (1 / (1 + access_count))

Default weights are ``w_sim = 0.4``, ``w_time = 0.4``, ``w_freq = 0.2`` so
the three terms sum to one. A value of 0.0 means the row is fresh,
relevant, and frequently read. A value near 1.0 means the row is old,
irrelevant to the current query, and untouched.

External dependencies (NOT installed by this module):
    pip install lancedb sentence-transformers datasketch simhash

The module imports the building blocks from the sibling modules
``memory.lancedb``, ``memory.embedders``, ``memory.reranker`` and
``memory.dedup`` so callers that already have a configured DB or
embedder can inject it via the ``Consolidator`` constructor instead of
the ``get_default_consolidator`` factory.

Usage:
    from memory.consolidator import get_default_consolidator
    cons = get_default_consolidator()
    result = cons.consolidate_new(
        text="lessons learned from debugger run 42",
        namespace="project",
        ttl_tier="lessons",
        metadata={"source": "review-agent"},
    )
    hits = cons.recall("what did we learn from run 42", top_k=5)
    telemetry = cons.consolidate_background(batch_size=200)
"""

from __future__ import annotations

import logging
import math
import os
import time
from pathlib import Path
from typing import Any

from memory.dedup import DedupPipeline
from memory.embedders import (
    CodeEmbedder,
    GeneralEmbedder,
    embed_both,
    get_code_embedder,
    get_general_embedder,
)
from memory.lancedb import (
    NAMESPACE_WEIGHTS,
    NAMESPACES,
    RRF_K,
    TTL_TIERS,
    MemoryDB,
    get_default_db,
)
from memory.reranker import Reranker, get_reranker


DEFAULT_LOG_PATH: str = "~/.opencode/memory.log"

DEFAULT_W_SIM: float = 0.4
DEFAULT_W_TIME: float = 0.4
DEFAULT_W_FREQ: float = 0.2

DEFAULT_LAMBDA_TIME: float = 0.01
DEFAULT_STALENESS_DROP: float = 0.9

DEFAULT_CANDIDATE_POOL: int = 20
DEFAULT_RECALL_TOP_K: int = 10
DEFAULT_RERANK_POOL: int = 20
DEFAULT_BACKGROUND_BATCH: int = 100

DEFAULT_NAMESPACE_PRIORITY: dict[str, float] = dict(NAMESPACE_WEIGHTS)


def _setup_logger() -> logging.Logger:
    expanded = os.path.expanduser(DEFAULT_LOG_PATH)
    Path(expanded).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("opencode.memory.consolidator")
    if not logger.handlers:
        handler = logging.FileHandler(expanded)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def _now_ts() -> float:
    return time.time()


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity with zero vector guard."""
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0
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


class StalenessScorer:
    """Park 2023 composite staleness score.

    The score combines three dimensions in a single weighted sum:

    * Query relevance: ``(1 - similarity_to_query)`` penalises rows that
      no longer match the current retrieval query.
    * Time decay: ``(1 - exp(-lambda_time * age_seconds))`` grows with
      age and saturates near 1.0 for very old rows.
    * Access frequency: ``(1 / (1 + access_count))`` punishes rows that
      have never been read since insertion and rewards frequently hit
      rows.

    Weights sum to 1.0 by default so the output stays bounded on
    ``[0, 1]``. Pass different weights on construction if a caller wants
    to emphasise one dimension (for example a retention policy that
    cares more about age than about relevance).
    """

    def __init__(
        self,
        w_sim: float = DEFAULT_W_SIM,
        w_time: float = DEFAULT_W_TIME,
        w_freq: float = DEFAULT_W_FREQ,
    ) -> None:
        total = float(w_sim) + float(w_time) + float(w_freq)
        if total <= 0.0:
            raise ValueError("staleness weights must sum to a positive value")
        self.w_sim = float(w_sim)
        self.w_time = float(w_time)
        self.w_freq = float(w_freq)
        self.logger = _setup_logger()

    def compute_staleness(
        self,
        entry: dict,
        now_ts: float,
        similarity_to_query: float,
        lambda_time: float = DEFAULT_LAMBDA_TIME,
    ) -> float:
        """Return a staleness score in ``[0.0, 1.0]`` for entry.

        Parameters:
            entry: a LanceDB row dict with ``created_ts`` and
                ``access_count`` fields.
            now_ts: seconds since epoch for the current wall clock.
            similarity_to_query: cosine similarity between the query
                embedding and the row embedding on the ``[0, 1]`` scale.
            lambda_time: exponential decay rate applied to age in
                seconds. Smaller values mean slower decay.
        """
        created = float(entry.get("created_ts", now_ts))
        access_count = int(entry.get("access_count", 0))

        sim = max(0.0, min(1.0, float(similarity_to_query)))
        sim_term = 1.0 - sim

        age = max(0.0, float(now_ts) - created)
        lam = max(0.0, float(lambda_time))
        time_term = 1.0 - math.exp(-lam * age)

        freq_term = 1.0 / (1.0 + max(0, access_count))

        total_w = self.w_sim + self.w_time + self.w_freq
        raw = (
            self.w_sim * sim_term
            + self.w_time * time_term
            + self.w_freq * freq_term
        )
        score = raw / total_w if total_w > 0.0 else raw
        score = max(0.0, min(1.0, float(score)))
        self.logger.info(
            "staleness sim=%.4f time=%.4f freq=%.4f score=%.4f",
            sim_term,
            time_term,
            freq_term,
            score,
        )
        return score


class Consolidator:
    """Compose the memory pipeline into a single high level surface.

    The consolidator owns references to a :class:`MemoryDB`, a general
    :class:`GeneralEmbedder`, a :class:`Reranker`, a
    :class:`DedupPipeline`, and a :class:`StalenessScorer`. Callers that
    already have these components wired can pass them in; otherwise use
    :func:`get_default_consolidator` to construct a fully wired default.

    Thread safety: the underlying components are not thread safe on
    their own. Callers must serialise access to a single Consolidator
    across threads or use one instance per worker.
    """

    def __init__(
        self,
        db: MemoryDB,
        embedder: GeneralEmbedder,
        reranker: Reranker,
        dedup_pipeline: DedupPipeline,
        staleness_scorer: StalenessScorer,
        code_embedder: CodeEmbedder | None = None,
        candidate_pool: int = DEFAULT_CANDIDATE_POOL,
    ) -> None:
        self.db = db
        self.embedder = embedder
        self.code_embedder = code_embedder
        self.reranker = reranker
        self.dedup = dedup_pipeline
        self.staleness = staleness_scorer
        self.candidate_pool = int(candidate_pool)
        self.logger = _setup_logger()
        self._contradictions = 0
        self.logger.info(
            "Consolidator init pool=%d w_sim=%.2f w_time=%.2f w_freq=%.2f",
            self.candidate_pool,
            self.staleness.w_sim,
            self.staleness.w_time,
            self.staleness.w_freq,
        )

    @property
    def contradictions(self) -> int:
        """Total contradictions detected so far by this instance."""
        return self._contradictions

    def _vector_candidates(
        self,
        general_vec: list[float],
        pool: int,
    ) -> list[dict]:
        """Top pool nearest rows for dedup candidate fetch."""
        try:
            return self.db.query_vector(
                embedding=general_vec,
                embedding_field="embedding_general",
                k=pool,
            )
        except Exception as exc:
            self.logger.warning("candidate vector query failed: %s", exc)
            return []

    def _merge_on_duplicate(self, matched_key: str) -> None:
        """Bump access metadata on a matched row without re inserting."""
        try:
            self.db.update_access(matched_key)
        except Exception as exc:
            self.logger.warning(
                "merge update_access failed key=%s err=%s", matched_key, exc
            )

    def _compute_embeddings(self, text: str) -> dict[str, list[float]]:
        """Run general plus code encoders, fall back to duplication on fail."""
        try:
            if self.code_embedder is not None:
                general_vec = self.embedder.embed(text)
                code_vec = self.code_embedder.embed(text)
                return {"general": general_vec, "code": code_vec}
            return embed_both(text)
        except Exception as exc:
            self.logger.warning(
                "embed_both failed, retrying general only: %s", exc
            )
            general_vec = self.embedder.embed(text)
            return {"general": general_vec, "code": general_vec}

    def consolidate_new(
        self,
        text: str,
        namespace: str,
        ttl_tier: str,
        metadata: dict | None = None,
    ) -> dict:
        """Insert text after a full dedup pass.

        Steps:
            1. Validate namespace and ttl_tier arguments.
            2. Compute dense embeddings (general plus code).
            3. Pull the top ``candidate_pool`` nearest existing rows by
               general vector as the dedup candidate set.
            4. Register the incoming text in the dedup pipeline so stage
               2 (MinHash LSH) sees it, then run ``check``.
            5. On a duplicate hit: bump access metadata on the matched
               row and return without inserting.
            6. On a contradiction verdict from the semantic stage: log
               the conflict, increment the contradictions counter, and
               still insert the new row so both sides remain queryable.
            7. On a miss: compute the SimHash fingerprint and insert.

        Returns a dict with the following shape::

            {
                "inserted": bool,
                "merged_with": str | None,
                "contradiction": bool,
                "id": str | None,
                "stage": str,
            }
        """
        if namespace not in NAMESPACES:
            raise ValueError(
                f"namespace must be one of {NAMESPACES}, got {namespace!r}"
            )
        if ttl_tier not in TTL_TIERS:
            raise ValueError(
                f"ttl_tier must be one of {TTL_TIERS}, got {ttl_tier!r}"
            )
        meta = dict(metadata or {})

        embeddings = self._compute_embeddings(text)
        general_vec = embeddings["general"]

        candidates = self._vector_candidates(general_vec, self.candidate_pool)
        candidate_tuples: list[tuple[str, str, int]] = []
        for row in candidates:
            rid = row.get("id")
            if not rid:
                continue
            row_text = row.get("text", "")
            row_fp = int(row.get("simhash_64", 0))
            candidate_tuples.append((str(rid), str(row_text), row_fp))

        new_fp = self.dedup.simhash.compute(text)

        pending_key = f"pending-{int(time.time() * 1_000_000)}"
        try:
            self.dedup.register(pending_key, text)
        except Exception as exc:
            self.logger.warning(
                "dedup register failed key=%s err=%s", pending_key, exc
            )

        verdict = self.dedup.check(text, candidate_tuples)
        if self.dedup.minhash is not None:
            try:
                self.dedup.minhash.remove(pending_key)
            except Exception:
                pass

        is_duplicate = bool(verdict.get("is_duplicate", False))
        is_contradiction = bool(verdict.get("contradiction", False))
        matched_key = verdict.get("matched_key")
        stage = str(verdict.get("stage", "none"))

        if is_duplicate and matched_key and not is_contradiction:
            self._merge_on_duplicate(str(matched_key))
            self.logger.info(
                "consolidate_new merged stage=%s matched=%s ns=%s tier=%s",
                stage,
                matched_key,
                namespace,
                ttl_tier,
            )
            return {
                "inserted": False,
                "merged_with": str(matched_key),
                "contradiction": False,
                "id": None,
                "stage": stage,
            }

        if is_contradiction:
            self._contradictions += 1
            self.logger.warning(
                "consolidate_new contradiction matched=%s ns=%s tier=%s total=%d",
                matched_key,
                namespace,
                ttl_tier,
                self._contradictions,
            )
            meta = {
                **meta,
                "contradiction_with": str(matched_key) if matched_key else "",
            }

        entry_id = self.db.add(
            text=text,
            namespace=namespace,
            ttl_tier=ttl_tier,
            embeddings={"general": general_vec, "code": embeddings["code"]},
            simhash=int(new_fp),
            metadata=meta,
        )
        self.logger.info(
            "consolidate_new inserted id=%s ns=%s tier=%s contradiction=%s",
            entry_id,
            namespace,
            ttl_tier,
            is_contradiction,
        )
        return {
            "inserted": True,
            "merged_with": None,
            "contradiction": is_contradiction,
            "id": entry_id,
            "stage": stage,
        }

    def _apply_namespace_priority(
        self,
        rows: list[dict],
        priority: dict[str, float],
    ) -> list[dict]:
        """Multiply rerank_score by namespace priority in place on copies."""
        boosted: list[dict] = []
        for row in rows:
            ns = str(row.get("namespace", ""))
            weight = float(priority.get(ns, 0.0))
            enriched = dict(row)
            base = float(enriched.get("rerank_score", 0.0))
            enriched["namespace_weight"] = weight
            enriched["final_score"] = base * weight
            boosted.append(enriched)
        boosted.sort(key=lambda r: r["final_score"], reverse=True)
        return boosted

    def recall(
        self,
        query: str,
        namespace_priority: dict[str, float] | None = None,
        top_k: int = DEFAULT_RECALL_TOP_K,
    ) -> list[dict]:
        """Hybrid retrieve + rerank with namespace priority weighting.

        Steps:
            1. Embed the query with the general encoder.
            2. Call ``db.query_hybrid`` with RRF at k=60 to fuse BM25 +
               dense results into a broad pool.
            3. Rerank the top ``DEFAULT_RERANK_POOL`` fused hits with
               the cross encoder so the ordering reflects semantic fit.
            4. Multiply the rerank_score by the namespace priority to
               bias session rows over project rows over global rows.
            5. Sort and return the top_k rows. Each row carries
               ``rrf_score``, ``rerank_score``, ``namespace_weight`` and
               ``final_score`` for downstream audit.
        """
        priority = dict(namespace_priority or DEFAULT_NAMESPACE_PRIORITY)
        query_vec = self.embedder.embed(query)
        fused = self.db.query_hybrid(
            query=query,
            general_embedding=query_vec,
            k=RRF_K,
            namespace_filter=None,
        )
        if not fused:
            self.logger.info("recall empty fused query_len=%d", len(query))
            return []

        pool = fused[: max(1, DEFAULT_RERANK_POOL)]
        reranked = self.reranker.rerank(
            query=query, candidates=pool, top_k=len(pool), text_field="text"
        )
        boosted = self._apply_namespace_priority(reranked, priority)
        out = boosted[: max(0, int(top_k))]

        for row in out:
            rid = row.get("id")
            if rid:
                try:
                    self.db.update_access(str(rid))
                except Exception as exc:
                    self.logger.warning(
                        "recall update_access failed id=%s err=%s", rid, exc
                    )

        self.logger.info(
            "recall fused=%d reranked=%d returned=%d top_k=%d",
            len(fused),
            len(reranked),
            len(out),
            top_k,
        )
        return out

    def consolidate_background(
        self,
        batch_size: int = DEFAULT_BACKGROUND_BATCH,
        staleness_drop: float = DEFAULT_STALENESS_DROP,
    ) -> dict[str, int]:
        """Delete rows whose composite staleness crosses the drop threshold.

        The background pass does not run a query against the store; it
        uses the row's own stored embedding as the "query" vector so the
        relevance term reduces to a self comparison of 1.0 and the
        staleness formula collapses onto the time and frequency terms.
        The formula still runs the full weighted sum so that callers
        that override the weights get consistent behaviour.

        Returns a telemetry dict with counts per namespace and tier plus
        a grand total so daemon telemetry can surface consolidation
        behaviour.
        """
        now = _now_ts()
        dropped_total = 0
        dropped_by_ns = {ns: 0 for ns in NAMESPACES}
        dropped_by_tier = {t: 0 for t in TTL_TIERS}

        try:
            rows = (
                self.db._entries()
                .search()
                .limit(max(1, int(batch_size)))
                .to_list()
            )
        except Exception as exc:
            self.logger.warning("background scan failed: %s", exc)
            return {
                "total_dropped": 0,
                "by_namespace": dropped_by_ns,
                "by_ttl_tier": dropped_by_tier,
                "scanned": 0,
            }

        scanned = 0
        for row in rows:
            rid = row.get("id")
            if not rid:
                continue
            scanned += 1
            own_vec = list(row.get("embedding_general", []) or [])
            sim = _cosine(own_vec, own_vec) if own_vec else 0.0
            score = self.staleness.compute_staleness(
                entry=row,
                now_ts=now,
                similarity_to_query=sim,
                lambda_time=DEFAULT_LAMBDA_TIME,
            )
            if score > float(staleness_drop):
                safe = str(rid).replace("'", "''")
                try:
                    self.db._entries().delete(f"id = '{safe}'")
                    self.db._stats().delete(f"entry_id = '{safe}'")
                    dropped_total += 1
                    ns = str(row.get("namespace", ""))
                    tier = str(row.get("ttl_tier", ""))
                    if ns in dropped_by_ns:
                        dropped_by_ns[ns] += 1
                    if tier in dropped_by_tier:
                        dropped_by_tier[tier] += 1
                    self.logger.info(
                        "background drop id=%s score=%.4f ns=%s tier=%s",
                        rid,
                        score,
                        ns,
                        tier,
                    )
                except Exception as exc:
                    self.logger.warning(
                        "background delete failed id=%s err=%s", rid, exc
                    )

        telemetry = {
            "total_dropped": dropped_total,
            "by_namespace": dropped_by_ns,
            "by_ttl_tier": dropped_by_tier,
            "scanned": scanned,
        }
        self.logger.info(
            "background scan=%d dropped=%d threshold=%.2f",
            scanned,
            dropped_total,
            staleness_drop,
        )
        return telemetry


_default_consolidator: Consolidator | None = None


def get_default_consolidator() -> Consolidator:
    """Return a process wide Consolidator singleton with lazy init.

    The singleton wires the default LanceDB store, general and code
    embedders, cross encoder reranker, three stage dedup pipeline, and
    a Park 2023 staleness scorer with the default weights. Callers that
    need custom weights or thresholds should build a Consolidator
    directly instead of using this factory.
    """
    global _default_consolidator
    if _default_consolidator is None:
        db = get_default_db()
        embedder = get_general_embedder()
        code = get_code_embedder()
        reranker = get_reranker()
        pipeline = DedupPipeline(embedder=embedder)
        scorer = StalenessScorer(
            w_sim=DEFAULT_W_SIM,
            w_time=DEFAULT_W_TIME,
            w_freq=DEFAULT_W_FREQ,
        )
        _default_consolidator = Consolidator(
            db=db,
            embedder=embedder,
            reranker=reranker,
            dedup_pipeline=pipeline,
            staleness_scorer=scorer,
            code_embedder=code,
        )
    return _default_consolidator


def reset_default_consolidator() -> None:
    """Reset the module singleton. Intended for tests."""
    global _default_consolidator
    _default_consolidator = None


def get_staleness_scorer(
    w_sim: float = DEFAULT_W_SIM,
    w_time: float = DEFAULT_W_TIME,
    w_freq: float = DEFAULT_W_FREQ,
) -> StalenessScorer:
    """Construct a fresh StalenessScorer with the given weights."""
    return StalenessScorer(w_sim=w_sim, w_time=w_time, w_freq=w_freq)


__all__ = [
    "Consolidator",
    "DEFAULT_BACKGROUND_BATCH",
    "DEFAULT_CANDIDATE_POOL",
    "DEFAULT_LAMBDA_TIME",
    "DEFAULT_NAMESPACE_PRIORITY",
    "DEFAULT_RECALL_TOP_K",
    "DEFAULT_RERANK_POOL",
    "DEFAULT_STALENESS_DROP",
    "DEFAULT_W_FREQ",
    "DEFAULT_W_SIM",
    "DEFAULT_W_TIME",
    "StalenessScorer",
    "get_default_consolidator",
    "get_staleness_scorer",
    "reset_default_consolidator",
]


def _self_check() -> dict[str, Any]:
    """Return a tiny diagnostic dict for CLI smoke tests.

    Does not hit the DB or load any ML models. Validates that the
    module imports and the staleness math is well formed on a synthetic
    entry.
    """
    scorer = StalenessScorer()
    now = _now_ts()
    entry = {
        "created_ts": now - 3600.0,
        "access_count": 2,
    }
    score = scorer.compute_staleness(
        entry=entry,
        now_ts=now,
        similarity_to_query=0.5,
        lambda_time=DEFAULT_LAMBDA_TIME,
    )
    return {
        "ok": True,
        "staleness": score,
        "weights": {
            "w_sim": scorer.w_sim,
            "w_time": scorer.w_time,
            "w_freq": scorer.w_freq,
        },
    }


if __name__ == "__main__":
    diag = _self_check()
    print(diag)
