"""LanceDB wrapper for the opencode-framework RAG memory system.

This module provides an embedded, file-backed memory store using LanceDB
as the underlying columnar vector database. LanceDB gives us native FTS
(BM25) alongside dense vector search in a single ACID/MVCC container,
which lets the agent framework run retrieval without a separate server.

Design notes:
    * Embedded LanceDB, single file-directory under ~/.opencode/memory.lancedb.
    * Hard cap at 2 GB resident RAM via the LANCEDB_MEMORY_LIMIT_GB env var.
      The cap is advisory for the LanceDB runtime; the process still relies
      on the host OS to enforce it, but we surface the value for visibility.
    * Three namespaces with fixed priority weights used by the retrieval
      ranker (not by LanceDB itself):
        session = 1.0, project = 0.7, global = 0.4.
    * Four TTL tiers drive time based eviction in expire_ttl():
        logs     =  7 days
        traces   = 30 days
        diffs    = 60 days
        lessons  = 180 days
    * Two parallel vector columns:
        embedding_general  VECTOR(1024)  (Qwen3-Embedding-0.6B)
        embedding_code     VECTOR(512)   (jina code embeddings 0.5B)
    * Hybrid retrieval: BM25 rank + dense vector rank fused via
      Reciprocal Rank Fusion with k = 60.
    * simhash_64 is stored alongside each row to allow near duplicate
      suppression by the caller (this module does not suppress; it only
      stores the value).

External dependencies (NOT installed by this module):
    pip install lancedb sentence-transformers datasketch simhash

Usage:
    from memory.lancedb import get_default_db
    db = get_default_db()
    db.add(
        text="example lesson",
        namespace="project",
        ttl_tier="lessons",
        embeddings={"general": [...], "code": [...]},
        simhash=123456789,
        metadata={"source": "review-agent"},
    )
    hits = db.query_hybrid(
        query="example",
        general_embedding=[...],
        k=60,
        namespace_filter=["session", "project"],
    )
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

try:
    import lancedb
except ImportError as exc:
    raise ImportError(
        "lancedb is required for memory.lancedb. "
        "Install with: pip install lancedb"
    ) from exc


NAMESPACES: tuple[str, ...] = ("session", "project", "global")
NAMESPACE_WEIGHTS: dict[str, float] = {
    "session": 1.0,
    "project": 0.7,
    "global": 0.4,
}

TTL_TIERS: tuple[str, ...] = ("logs", "traces", "diffs", "lessons")
TTL_DAYS: dict[str, int] = {
    "logs": 7,
    "traces": 30,
    "diffs": 60,
    "lessons": 180,
}

DEFAULT_DB_PATH: str = "~/.opencode/memory.lancedb"
DEFAULT_LOG_PATH: str = "~/.opencode/memory.log"
DEFAULT_MAX_RAM_GB: float = 2.0

VECTOR_DIM_GENERAL: int = 1024
VECTOR_DIM_CODE: int = 512

RRF_K: int = 60

TABLE_ENTRIES: str = "memory_entries"
TABLE_FTS_INDEX: str = "memory_fts_index"
TABLE_STATS: str = "memory_stats"


def _now_ts() -> float:
    return time.time()


def _setup_logger(log_path: str) -> logging.Logger:
    expanded = os.path.expanduser(log_path)
    Path(expanded).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("opencode.memory.lancedb")
    if not logger.handlers:
        handler = logging.FileHandler(expanded)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class MemoryDB:
    """LanceDB backed memory store for the RAG pipeline."""

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        max_ram_gb: float = DEFAULT_MAX_RAM_GB,
    ) -> None:
        self.db_path = os.path.expanduser(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.max_ram_gb = float(max_ram_gb)
        os.environ["LANCEDB_MEMORY_LIMIT_GB"] = str(self.max_ram_gb)
        self.logger = _setup_logger(DEFAULT_LOG_PATH)
        self.logger.info(
            "MemoryDB init path=%s ram_cap_gb=%s", self.db_path, self.max_ram_gb
        )
        self.client = lancedb.connect(self.db_path)
        self._entries_table = None
        self._stats_table = None

    def ensure_schema(self) -> None:
        """Create the three tables if missing."""
        existing = set(self.client.table_names())

        if TABLE_ENTRIES not in existing:
            sample = [
                {
                    "id": "bootstrap",
                    "text": "",
                    "namespace": "session",
                    "ttl_tier": "logs",
                    "created_ts": _now_ts(),
                    "accessed_ts": _now_ts(),
                    "access_count": 0,
                    "embedding_general": [0.0] * VECTOR_DIM_GENERAL,
                    "embedding_code": [0.0] * VECTOR_DIM_CODE,
                    "simhash_64": 0,
                    "metadata": "{}",
                }
            ]
            self._entries_table = self.client.create_table(
                TABLE_ENTRIES, data=sample
            )
            self._entries_table.delete("id = 'bootstrap'")
            try:
                self._entries_table.create_fts_index("text", replace=True)
            except Exception as fts_exc:
                self.logger.warning("FTS index creation skipped: %s", fts_exc)
            self.logger.info("Created table %s", TABLE_ENTRIES)
        else:
            self._entries_table = self.client.open_table(TABLE_ENTRIES)

        if TABLE_FTS_INDEX not in existing:
            fts_bootstrap = [
                {"id": "bootstrap", "text": "", "created_ts": _now_ts()}
            ]
            tbl = self.client.create_table(TABLE_FTS_INDEX, data=fts_bootstrap)
            tbl.delete("id = 'bootstrap'")
            try:
                tbl.create_fts_index("text", replace=True)
            except Exception as fts_exc:
                self.logger.warning(
                    "Secondary FTS index creation skipped: %s", fts_exc
                )
            self.logger.info("Created table %s", TABLE_FTS_INDEX)

        if TABLE_STATS not in existing:
            stats_bootstrap = [
                {
                    "entry_id": "bootstrap",
                    "last_access_ts": _now_ts(),
                    "access_count": 0,
                }
            ]
            self._stats_table = self.client.create_table(
                TABLE_STATS, data=stats_bootstrap
            )
            self._stats_table.delete("entry_id = 'bootstrap'")
            self.logger.info("Created table %s", TABLE_STATS)
        else:
            self._stats_table = self.client.open_table(TABLE_STATS)

    def _entries(self):
        if self._entries_table is None:
            self.ensure_schema()
        return self._entries_table

    def _stats(self):
        if self._stats_table is None:
            self.ensure_schema()
        return self._stats_table

    def add(
        self,
        text: str,
        namespace: str,
        ttl_tier: str,
        embeddings: dict,
        simhash: int,
        metadata: dict,
    ) -> str:
        """Insert a single memory row, returning the generated id."""
        if namespace not in NAMESPACES:
            raise ValueError(
                f"namespace must be one of {NAMESPACES}, got {namespace!r}"
            )
        if ttl_tier not in TTL_TIERS:
            raise ValueError(
                f"ttl_tier must be one of {TTL_TIERS}, got {ttl_tier!r}"
            )
        g_vec = embeddings.get("general")
        c_vec = embeddings.get("code")
        if g_vec is None or len(g_vec) != VECTOR_DIM_GENERAL:
            raise ValueError(
                f"embeddings['general'] must be length {VECTOR_DIM_GENERAL}"
            )
        if c_vec is None or len(c_vec) != VECTOR_DIM_CODE:
            raise ValueError(
                f"embeddings['code'] must be length {VECTOR_DIM_CODE}"
            )

        entry_id = str(uuid.uuid4())
        now = _now_ts()
        row = {
            "id": entry_id,
            "text": text,
            "namespace": namespace,
            "ttl_tier": ttl_tier,
            "created_ts": now,
            "accessed_ts": now,
            "access_count": 0,
            "embedding_general": list(g_vec),
            "embedding_code": list(c_vec),
            "simhash_64": int(simhash),
            "metadata": json.dumps(metadata or {}),
        }
        self._entries().add([row])
        self._stats().add(
            [
                {
                    "entry_id": entry_id,
                    "last_access_ts": now,
                    "access_count": 0,
                }
            ]
        )
        self.logger.info(
            "add id=%s ns=%s tier=%s len_text=%d",
            entry_id,
            namespace,
            ttl_tier,
            len(text),
        )
        return entry_id

    def query_vector(
        self,
        embedding: list[float],
        embedding_field: str = "embedding_general",
        k: int = RRF_K,
    ) -> list[dict]:
        """Dense nearest neighbor lookup over a single embedding column."""
        if embedding_field not in ("embedding_general", "embedding_code"):
            raise ValueError(
                "embedding_field must be embedding_general or embedding_code"
            )
        results = (
            self._entries()
            .search(list(embedding), vector_column_name=embedding_field)
            .limit(k)
            .to_list()
        )
        self.logger.info(
            "query_vector field=%s k=%d hits=%d",
            embedding_field,
            k,
            len(results),
        )
        return results

    def query_fts(self, query: str, k: int = RRF_K) -> list[dict]:
        """BM25 full text lookup over the text column."""
        try:
            results = (
                self._entries()
                .search(query, query_type="fts")
                .limit(k)
                .to_list()
            )
        except Exception as fts_exc:
            self.logger.warning(
                "FTS query failed, falling back to contains: %s", fts_exc
            )
            safe = query.replace("'", "''")
            results = (
                self._entries()
                .search()
                .where(f"text LIKE '%{safe}%'")
                .limit(k)
                .to_list()
            )
        self.logger.info("query_fts q_len=%d k=%d hits=%d", len(query), k, len(results))
        return results

    def query_hybrid(
        self,
        query: str,
        general_embedding: list[float],
        k: int = RRF_K,
        namespace_filter: list[str] | None = None,
    ) -> list[dict]:
        """Hybrid BM25 + dense lookup with Reciprocal Rank Fusion.

        rrf_score = sum over lists of (1 / (RRF_K + rank_i))

        namespace_filter is applied post fetch so both branches run against
        the full pool and rank fairly.
        """
        fts_hits = self.query_fts(query, k=k)
        dense_hits = self.query_vector(
            general_embedding, embedding_field="embedding_general", k=k
        )

        def _filter(rows: Iterable[dict]) -> list[dict]:
            if not namespace_filter:
                return list(rows)
            allowed = set(namespace_filter)
            return [r for r in rows if r.get("namespace") in allowed]

        fts_hits = _filter(fts_hits)
        dense_hits = _filter(dense_hits)

        scores: dict[str, float] = {}
        payload: dict[str, dict] = {}
        for rank, row in enumerate(fts_hits):
            rid = row.get("id")
            if rid is None:
                continue
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (RRF_K + rank + 1)
            payload.setdefault(rid, row)
        for rank, row in enumerate(dense_hits):
            rid = row.get("id")
            if rid is None:
                continue
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (RRF_K + rank + 1)
            payload.setdefault(rid, row)

        fused = sorted(
            ({"rrf_score": s, **payload[rid]} for rid, s in scores.items()),
            key=lambda r: r["rrf_score"],
            reverse=True,
        )[:k]
        self.logger.info(
            "query_hybrid k=%d fts=%d dense=%d fused=%d",
            k,
            len(fts_hits),
            len(dense_hits),
            len(fused),
        )
        return fused

    def update_access(self, entry_id: str) -> None:
        """Bump accessed_ts and access_count for staleness tracking."""
        now = _now_ts()
        safe = entry_id.replace("'", "''")
        rows = (
            self._entries()
            .search()
            .where(f"id = '{safe}'")
            .limit(1)
            .to_list()
        )
        if not rows:
            self.logger.warning("update_access missing id=%s", entry_id)
            return
        current = rows[0]
        new_count = int(current.get("access_count", 0)) + 1
        try:
            self._entries().update(
                where=f"id = '{safe}'",
                values={"accessed_ts": now, "access_count": new_count},
            )
        except Exception as upd_exc:
            self.logger.warning(
                "update_access update failed id=%s err=%s", entry_id, upd_exc
            )
        try:
            self._stats().update(
                where=f"entry_id = '{safe}'",
                values={"last_access_ts": now, "access_count": new_count},
            )
        except Exception:
            self._stats().add(
                [
                    {
                        "entry_id": entry_id,
                        "last_access_ts": now,
                        "access_count": new_count,
                    }
                ]
            )
        self.logger.info(
            "update_access id=%s count=%d", entry_id, new_count
        )

    def expire_ttl(self) -> dict[str, int]:
        """Delete rows older than the per tier TTL. Returns counts deleted."""
        now = _now_ts()
        deleted: dict[str, int] = {}
        for tier, days in TTL_DAYS.items():
            cutoff = now - days * 86400
            before = (
                self._entries()
                .search()
                .where(f"ttl_tier = '{tier}' AND created_ts < {cutoff}")
                .limit(1_000_000)
                .to_list()
            )
            count = len(before)
            if count > 0:
                try:
                    self._entries().delete(
                        f"ttl_tier = '{tier}' AND created_ts < {cutoff}"
                    )
                except Exception as del_exc:
                    self.logger.warning(
                        "expire_ttl delete failed tier=%s err=%s", tier, del_exc
                    )
                    count = 0
            deleted[tier] = count
            self.logger.info(
                "expire_ttl tier=%s days=%d deleted=%d", tier, days, count
            )
        return deleted

    def stats(self) -> dict[str, Any]:
        """Row counts per namespace and tier."""
        rows = (
            self._entries().search().limit(10_000_000).to_list()
        )
        by_ns: dict[str, int] = {n: 0 for n in NAMESPACES}
        by_tier: dict[str, int] = {t: 0 for t in TTL_TIERS}
        for r in rows:
            ns = r.get("namespace")
            tier = r.get("ttl_tier")
            if ns in by_ns:
                by_ns[ns] += 1
            if tier in by_tier:
                by_tier[tier] += 1
        result = {
            "total": len(rows),
            "by_namespace": by_ns,
            "by_ttl_tier": by_tier,
            "db_path": self.db_path,
            "ram_cap_gb": self.max_ram_gb,
        }
        self.logger.info("stats total=%d", len(rows))
        return result


_default_db: MemoryDB | None = None


def get_default_db() -> MemoryDB:
    """Return a process wide singleton MemoryDB with lazy init."""
    global _default_db
    if _default_db is None:
        _default_db = MemoryDB()
        _default_db.ensure_schema()
    return _default_db
