"""Time to live tier management for the opencode-framework RAG memory.

This module owns retention policy for the LanceDB backed memory store.
The underlying :mod:`memory.lancedb` module already exposes a simpler
``expire_ttl`` helper; this module extends it with:

* Access driven tier promotion so rows that are read frequently live
  longer than the default per tier budget.
* Per tier statistics including rows that will expire in the next 24
  hours so operators can see what is about to drop before it drops.
* A ``schedule_expiry`` entrypoint that a cron job or the opencode
  daemon can invoke once per day. It runs a full ``expire_all`` pass
  across every tier, pulls stats, and appends a structured log line to
  ``~/.opencode/ttl.log`` for audit.

Tier budgets (also exposed via :data:`TTL_TIERS`):

+----------+--------+---------+
| Tier     | Days   | Seconds |
+==========+========+=========+
| logs     |     7  |  604800 |
+----------+--------+---------+
| traces   |    30  | 2592000 |
+----------+--------+---------+
| diffs    |    60  | 5184000 |
+----------+--------+---------+
| lessons  |   180  |15552000 |
+----------+--------+---------+

Tier promotion rule (:meth:`TTLManager.tier_extensions`):
    when a row's ``access_count`` is greater than 10 and its current
    tier is not already ``lessons``, the tier is promoted one step
    along ``logs -> traces -> diffs -> lessons``. Promotion lets
    frequently read rows live longer without moving them out of the
    normal expiry pipeline.

External dependencies: none beyond the Python 3 stdlib and the sibling
``memory.lancedb`` module. The LanceDB runtime is imported transitively
through :func:`memory.lancedb.get_default_db`.

Usage:
    from memory.ttl import TTLManager, schedule_expiry
    mgr = TTLManager(db=None)
    stats_before = mgr.stats()
    mgr.expire_all()
    mgr.tier_extensions()
    stats_after = mgr.stats()

    # Cron friendly one shot:
    if __name__ == "__main__":
        schedule_expiry()
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from memory.lancedb import MemoryDB, TTL_TIERS as LANCEDB_TIERS, get_default_db


TTL_TIERS: dict[str, int] = {
    "logs": 7 * 86400,
    "traces": 30 * 86400,
    "diffs": 60 * 86400,
    "lessons": 180 * 86400,
}

PROMOTION_CHAIN: tuple[str, ...] = ("logs", "traces", "diffs", "lessons")
PROMOTION_ACCESS_THRESHOLD: int = 10

DEFAULT_TTL_LOG_PATH: str = "~/.opencode/ttl.log"
DEFAULT_MEMORY_LOG_PATH: str = "~/.opencode/memory.log"

STATS_EXPIRING_HORIZON_SECONDS: int = 24 * 3600


def _setup_logger() -> logging.Logger:
    expanded = os.path.expanduser(DEFAULT_MEMORY_LOG_PATH)
    Path(expanded).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("opencode.memory.ttl")
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


def _ensure_log_dir(path: str) -> Path:
    expanded = Path(os.path.expanduser(path))
    expanded.parent.mkdir(parents=True, exist_ok=True)
    return expanded


class TTLManager:
    """Manage per tier retention on top of a :class:`MemoryDB`.

    Callers pass an existing :class:`MemoryDB` instance or ``None`` to
    pick up the process wide default from
    :func:`memory.lancedb.get_default_db`. Each method runs independent
    LanceDB mutations so the manager is safe to call from a cron style
    entrypoint or from inside a long running daemon.
    """

    def __init__(self, db: MemoryDB | None = None) -> None:
        self.db = db if db is not None else get_default_db()
        self.logger = _setup_logger()
        self.logger.info(
            "TTLManager init tiers=%s chain=%s",
            list(TTL_TIERS.keys()),
            list(PROMOTION_CHAIN),
        )

    def _rows_in_tier(self, tier: str) -> list[dict]:
        """Best effort fetch of every row currently tagged with tier."""
        safe = tier.replace("'", "''")
        try:
            return (
                self.db._entries()
                .search()
                .where(f"ttl_tier = '{safe}'")
                .limit(10_000_000)
                .to_list()
            )
        except Exception as exc:
            self.logger.warning(
                "rows_in_tier tier=%s fetch failed err=%s", tier, exc
            )
            return []

    def expire_tier(
        self,
        tier: str,
        now_ts: float | None = None,
    ) -> int:
        """Delete rows older than the tier budget. Returns deleted count.

        ``now_ts`` can be injected for deterministic tests. When left as
        ``None`` the wall clock is used. The tier must be one of the
        keys in :data:`TTL_TIERS`; a ``ValueError`` is raised otherwise.
        """
        if tier not in TTL_TIERS:
            raise ValueError(
                f"unknown tier {tier!r}. valid tiers: {list(TTL_TIERS.keys())}"
            )
        budget = TTL_TIERS[tier]
        now = float(now_ts) if now_ts is not None else _now_ts()
        cutoff = now - budget

        safe = tier.replace("'", "''")
        try:
            expired = (
                self.db._entries()
                .search()
                .where(f"ttl_tier = '{safe}' AND created_ts < {cutoff}")
                .limit(10_000_000)
                .to_list()
            )
        except Exception as exc:
            self.logger.warning(
                "expire_tier fetch failed tier=%s err=%s", tier, exc
            )
            return 0

        count = len(expired)
        if count == 0:
            self.logger.info(
                "expire_tier tier=%s cutoff=%.0f deleted=0", tier, cutoff
            )
            return 0

        try:
            self.db._entries().delete(
                f"ttl_tier = '{safe}' AND created_ts < {cutoff}"
            )
        except Exception as exc:
            self.logger.warning(
                "expire_tier delete failed tier=%s err=%s", tier, exc
            )
            return 0

        for row in expired:
            rid = row.get("id")
            if not rid:
                continue
            rid_safe = str(rid).replace("'", "''")
            try:
                self.db._stats().delete(f"entry_id = '{rid_safe}'")
            except Exception:
                pass

        self.logger.info(
            "expire_tier tier=%s cutoff=%.0f deleted=%d", tier, cutoff, count
        )
        return count

    def expire_all(self, now_ts: float | None = None) -> dict[str, int]:
        """Run :meth:`expire_tier` for every tier. Returns per tier counts."""
        now = float(now_ts) if now_ts is not None else _now_ts()
        result: dict[str, int] = {}
        for tier in TTL_TIERS:
            result[tier] = self.expire_tier(tier, now_ts=now)
        self.logger.info("expire_all result=%s", result)
        return result

    def tier_extensions(self) -> dict[str, int]:
        """Promote frequently accessed rows to the next tier up.

        Rule:
            * ``access_count > 10``
            * current tier is one of
              ``logs``, ``traces``, ``diffs``
              (``lessons`` is the top of the chain so it is left alone)

        Returns a dict counting how many rows were promoted out of each
        source tier. Promotion writes through :func:`MemoryDB._entries`
        with an ``update`` WHERE the row id matches so the LanceDB
        transaction stays scoped to the single affected row.
        """
        promotions: dict[str, int] = {t: 0 for t in PROMOTION_CHAIN}
        promotion_map = {
            PROMOTION_CHAIN[i]: PROMOTION_CHAIN[i + 1]
            for i in range(len(PROMOTION_CHAIN) - 1)
        }

        for source_tier, target_tier in promotion_map.items():
            rows = self._rows_in_tier(source_tier)
            for row in rows:
                access_count = int(row.get("access_count", 0))
                if access_count <= PROMOTION_ACCESS_THRESHOLD:
                    continue
                rid = row.get("id")
                if not rid:
                    continue
                safe = str(rid).replace("'", "''")
                try:
                    self.db._entries().update(
                        where=f"id = '{safe}'",
                        values={"ttl_tier": target_tier},
                    )
                    promotions[source_tier] += 1
                    self.logger.info(
                        "promotion id=%s %s -> %s count=%d",
                        rid,
                        source_tier,
                        target_tier,
                        access_count,
                    )
                except Exception as exc:
                    self.logger.warning(
                        "promotion update failed id=%s err=%s", rid, exc
                    )

        self.logger.info("tier_extensions promotions=%s", promotions)
        return promotions

    def stats(self) -> dict[str, Any]:
        """Return per tier counts plus rows expiring in the next 24 hours.

        The output shape is::

            {
                "totals": {tier: total_rows_in_tier},
                "expiring_soon": {tier: rows_expiring_in_24h},
                "horizon_seconds": 86400,
                "generated_ts": epoch_seconds,
            }

        Rows are considered "expiring soon" when
        ``now + 24h >= created_ts + tier_budget``.
        """
        now = _now_ts()
        totals: dict[str, int] = {}
        expiring: dict[str, int] = {}

        for tier, budget in TTL_TIERS.items():
            rows = self._rows_in_tier(tier)
            totals[tier] = len(rows)
            horizon = now + STATS_EXPIRING_HORIZON_SECONDS
            soon = 0
            for row in rows:
                created = float(row.get("created_ts", now))
                expires_at = created + float(budget)
                if expires_at <= horizon:
                    soon += 1
            expiring[tier] = soon

        out = {
            "totals": totals,
            "expiring_soon": expiring,
            "horizon_seconds": STATS_EXPIRING_HORIZON_SECONDS,
            "generated_ts": now,
        }
        self.logger.info(
            "stats totals=%s expiring_soon=%s", totals, expiring
        )
        return out


def schedule_expiry(
    ttl_log_path: str = DEFAULT_TTL_LOG_PATH,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Cron friendly one shot: run expire_all + tier_extensions + stats.

    Appends a JSON line to ``~/.opencode/ttl.log`` with the summary so
    an operator can ``tail -f`` the log during a rollout. Returns the
    same summary dict so callers that invoke this function in process
    can assert on the result.

    Designed to be idempotent: running it twice within a second causes
    the second run to find nothing to expire (because the first run
    already deleted the aged rows) and to log a zero counts summary.
    """
    mgr = TTLManager()
    now = float(now_ts) if now_ts is not None else _now_ts()
    expired = mgr.expire_all(now_ts=now)
    promoted = mgr.tier_extensions()
    stats = mgr.stats()

    summary = {
        "run_ts": now,
        "expired": expired,
        "promoted": promoted,
        "stats": stats,
    }

    log_path = _ensure_log_dir(ttl_log_path)
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(summary, sort_keys=True))
            fh.write("\n")
    except Exception as exc:
        mgr.logger.warning(
            "ttl log append failed path=%s err=%s", log_path, exc
        )

    mgr.logger.info(
        "schedule_expiry expired=%s promoted=%s totals=%s",
        expired,
        promoted,
        stats.get("totals", {}),
    )
    return summary


def _sanity_check() -> int:
    """Structural check that tier tables and the lancedb module agree."""
    problems = 0
    for tier in LANCEDB_TIERS:
        if tier not in TTL_TIERS:
            problems += 1
    for tier in TTL_TIERS:
        if tier not in LANCEDB_TIERS:
            problems += 1
    if set(PROMOTION_CHAIN) != set(TTL_TIERS.keys()):
        problems += 1
    return problems


__all__ = [
    "DEFAULT_TTL_LOG_PATH",
    "PROMOTION_ACCESS_THRESHOLD",
    "PROMOTION_CHAIN",
    "STATS_EXPIRING_HORIZON_SECONDS",
    "TTLManager",
    "TTL_TIERS",
    "schedule_expiry",
]


if __name__ == "__main__":
    problems = _sanity_check()
    if problems:
        print(
            "ttl sanity check failed: {} tier mismatches".format(problems),
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        summary = schedule_expiry()
        print(json.dumps(summary, sort_keys=True))
    except Exception as exc:
        print("schedule_expiry failed: {}".format(exc), file=sys.stderr)
        sys.exit(1)
