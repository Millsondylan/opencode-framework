#!/usr/bin/env python3
"""Nightly telemetry rollup for opencode-framework.

Reads raw event tables (agent_invocations, pipeline_runs, golden_results)
from the SQLite telemetry store and produces:

1. Daily rollup rows in daily_rollups.
2. Opus vs Sonnet model share.
3. 30 day token spend with a cost estimate.
4. Mean confidence over a configurable window.
5. Anomaly list flagged into anomaly_events.
6. A JSON snapshot consumed by telemetry/dashboard/index.html.

Zero banned dashes. ASCII hyphen only.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = ".claude/hooks/logs/telemetry.sqlite"
DEFAULT_SCHEMA_PATH = "telemetry/db.sql"
DEFAULT_DASHBOARD_JSON = "telemetry/dashboard/data/rollup.json"

# Published pricing per 1M output tokens. Update when pricing changes.
OPUS_PRICE_PER_MTOK_OUT = 75.0
SONNET_PRICE_PER_MTOK_OUT = 15.0
OPUS_PRICE_PER_MTOK_IN = 15.0
SONNET_PRICE_PER_MTOK_IN = 3.0

CONFIDENCE_FLOOR = 90.0
ERROR_RATE_CEILING = 0.05
LATENCY_SPIKE_FACTOR = 2.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return float(ordered[k])


class TelemetryRollup:
    """Aggregates raw event tables into daily summaries."""

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        schema_path: str = DEFAULT_SCHEMA_PATH,
    ) -> None:
        self.db_path = db_path
        self.schema_path = schema_path
        self._ensure_parent()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")

    def _ensure_parent(self) -> None:
        parent = Path(self.db_path).parent
        if str(parent) and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        try:
            self.conn.close()
        except sqlite3.Error:
            pass

    # -- schema ---------------------------------------------------------

    def apply_schema(self) -> None:
        """Execute db.sql against the connection."""
        schema = Path(self.schema_path).read_text(encoding="utf-8")
        self.conn.executescript(schema)
        self.conn.commit()

    # -- helpers --------------------------------------------------------

    def _query_all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        cur = self.conn.execute(sql, params)
        return list(cur.fetchall())

    def _query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        cur = self.conn.execute(sql, params)
        return cur.fetchone()

    # -- rollup ---------------------------------------------------------

    def run_rollup(self, date: str | None = None) -> dict[str, Any]:
        """Aggregate per agent stats for the given UTC date (YYYY-MM-DD).

        Returns the summary dict that was upserted into daily_rollups.
        """
        if date is None:
            date = datetime.now(timezone.utc).date().isoformat()

        day_start = f"{date}T00:00:00+00:00"
        day_end = f"{date}T23:59:59+00:00"

        rows = self._query_all(
            """
            SELECT tokens_in, tokens_out, duration_ms, confidence_score,
                   model, outcome
            FROM agent_invocations
            WHERE ts >= ? AND ts <= ?
            """,
            (day_start, day_end),
        )

        invocation_count = len(rows)
        tokens_in_total = sum(r["tokens_in"] or 0 for r in rows)
        tokens_out_total = sum(r["tokens_out"] or 0 for r in rows)
        confidences = [
            float(r["confidence_score"]) for r in rows if r["confidence_score"] is not None
        ]
        mean_conf = statistics.fmean(confidences) if confidences else None
        opus_count = sum(1 for r in rows if (r["model"] or "").startswith("claude-opus"))
        sonnet_count = sum(
            1 for r in rows if (r["model"] or "").startswith("claude-sonnet")
        )
        error_count = sum(1 for r in rows if (r["outcome"] or "") == "error")
        latencies = [float(r["duration_ms"] or 0) for r in rows]
        p95 = int(_percentile(latencies, 95.0)) if latencies else None

        record = {
            "rollup_date": date,
            "invocation_count": invocation_count,
            "tokens_in_total": tokens_in_total,
            "tokens_out_total": tokens_out_total,
            "mean_confidence": mean_conf,
            "opus_count": opus_count,
            "sonnet_count": sonnet_count,
            "error_count": error_count,
            "p95_latency_ms": p95,
            "generated_at": _now_iso(),
        }

        self.conn.execute(
            """
            INSERT INTO daily_rollups (
                rollup_date, invocation_count, tokens_in_total, tokens_out_total,
                mean_confidence, opus_count, sonnet_count, error_count,
                p95_latency_ms, generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rollup_date) DO UPDATE SET
                invocation_count = excluded.invocation_count,
                tokens_in_total  = excluded.tokens_in_total,
                tokens_out_total = excluded.tokens_out_total,
                mean_confidence  = excluded.mean_confidence,
                opus_count       = excluded.opus_count,
                sonnet_count     = excluded.sonnet_count,
                error_count      = excluded.error_count,
                p95_latency_ms   = excluded.p95_latency_ms,
                generated_at     = excluded.generated_at
            """,
            (
                record["rollup_date"],
                record["invocation_count"],
                record["tokens_in_total"],
                record["tokens_out_total"],
                record["mean_confidence"],
                record["opus_count"],
                record["sonnet_count"],
                record["error_count"],
                record["p95_latency_ms"],
                record["generated_at"],
            ),
        )
        self.conn.commit()
        return record

    # -- aggregates -----------------------------------------------------

    def compute_opus_sonnet_share(self) -> dict[str, float]:
        row = self._query_one(
            """
            SELECT
                SUM(CASE WHEN model LIKE 'claude-opus%'   THEN 1 ELSE 0 END) AS opus,
                SUM(CASE WHEN model LIKE 'claude-sonnet%' THEN 1 ELSE 0 END) AS sonnet,
                COUNT(*) AS total
            FROM agent_invocations
            """
        )
        if not row or not row["total"]:
            return {"opus": 0.0, "sonnet": 0.0, "total": 0}
        total = float(row["total"])
        return {
            "opus": round((row["opus"] or 0) / total * 100.0, 2),
            "sonnet": round((row["sonnet"] or 0) / total * 100.0, 2),
            "total": int(total),
        }

    def compute_token_spend(self, days: int = 30) -> dict[str, Any]:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).isoformat(timespec="seconds")
        rows = self._query_all(
            """
            SELECT model, tokens_in, tokens_out
            FROM agent_invocations
            WHERE ts >= ?
            """,
            (cutoff,),
        )
        opus_in = opus_out = sonnet_in = sonnet_out = 0
        for r in rows:
            model = r["model"] or ""
            t_in = r["tokens_in"] or 0
            t_out = r["tokens_out"] or 0
            if model.startswith("claude-opus"):
                opus_in += t_in
                opus_out += t_out
            elif model.startswith("claude-sonnet"):
                sonnet_in += t_in
                sonnet_out += t_out
        cost = (
            opus_in * OPUS_PRICE_PER_MTOK_IN / 1_000_000.0
            + opus_out * OPUS_PRICE_PER_MTOK_OUT / 1_000_000.0
            + sonnet_in * SONNET_PRICE_PER_MTOK_IN / 1_000_000.0
            + sonnet_out * SONNET_PRICE_PER_MTOK_OUT / 1_000_000.0
        )
        return {
            "window_days": days,
            "opus_tokens_in": opus_in,
            "opus_tokens_out": opus_out,
            "sonnet_tokens_in": sonnet_in,
            "sonnet_tokens_out": sonnet_out,
            "total_tokens": opus_in + opus_out + sonnet_in + sonnet_out,
            "estimated_cost_usd": round(cost, 4),
        }

    def compute_mean_confidence(self, days: int = 7) -> float:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).isoformat(timespec="seconds")
        row = self._query_one(
            """
            SELECT AVG(CAST(confidence_score AS REAL)) AS mc
            FROM agent_invocations
            WHERE ts >= ? AND confidence_score IS NOT NULL
            """,
            (cutoff,),
        )
        if not row or row["mc"] is None:
            return 0.0
        return float(row["mc"])

    # -- anomalies ------------------------------------------------------

    def detect_anomalies(self) -> list[str]:
        anomalies: list[str] = []

        mean_conf_7d = self.compute_mean_confidence(days=7)
        if mean_conf_7d and mean_conf_7d < CONFIDENCE_FLOOR:
            anomalies.append(
                f"low_confidence: 7d mean confidence is {mean_conf_7d:.2f}, "
                f"below floor {CONFIDENCE_FLOOR}"
            )

        row = self._query_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN outcome = 'error' THEN 1 ELSE 0 END) AS errors
            FROM agent_invocations
            WHERE ts >= ?
            """,
            ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds"),),
        )
        if row and row["total"]:
            total = int(row["total"])
            errors = int(row["errors"] or 0)
            if total > 0:
                rate = errors / total
                if rate > ERROR_RATE_CEILING:
                    anomalies.append(
                        f"error_rate: 24h error rate is {rate:.2%}, "
                        f"above ceiling {ERROR_RATE_CEILING:.0%}"
                    )

        latencies_recent = [
            float(r["duration_ms"] or 0)
            for r in self._query_all(
                """
                SELECT duration_ms FROM agent_invocations
                WHERE ts >= ?
                """,
                (
                    (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(
                        timespec="seconds"
                    ),
                ),
            )
        ]
        latencies_baseline = [
            float(r["duration_ms"] or 0)
            for r in self._query_all(
                """
                SELECT duration_ms FROM agent_invocations
                WHERE ts >= ? AND ts < ?
                """,
                (
                    (datetime.now(timezone.utc) - timedelta(days=14)).isoformat(
                        timespec="seconds"
                    ),
                    (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(
                        timespec="seconds"
                    ),
                ),
            )
        ]
        if latencies_recent and latencies_baseline:
            p95_recent = _percentile(latencies_recent, 95.0)
            p95_base = _percentile(latencies_baseline, 95.0)
            if p95_base > 0 and p95_recent > p95_base * LATENCY_SPIKE_FACTOR:
                anomalies.append(
                    f"latency_spike: p95 is {p95_recent:.0f}ms vs baseline "
                    f"{p95_base:.0f}ms (factor {LATENCY_SPIKE_FACTOR})"
                )

        now = _now_iso()
        for msg in anomalies:
            kind = msg.split(":", 1)[0]
            self.conn.execute(
                """
                INSERT INTO anomaly_events (ts, kind, severity, message, resolved)
                VALUES (?, ?, 'warning', ?, 0)
                """,
                (now, kind, msg),
            )
        self.conn.commit()
        return anomalies

    # -- dashboard export ----------------------------------------------

    def export_for_dashboard(self, out_path: str) -> dict[str, Any]:
        """Write a JSON snapshot for the static dashboard."""
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        share = self.compute_opus_sonnet_share()
        spend = self.compute_token_spend(days=30)
        mean_conf = self.compute_mean_confidence(days=7)

        daily = self._query_all(
            """
            SELECT rollup_date, invocation_count, tokens_in_total, tokens_out_total,
                   mean_confidence, opus_count, sonnet_count, error_count,
                   p95_latency_ms
            FROM daily_rollups
            ORDER BY rollup_date DESC
            LIMIT 30
            """
        )

        runs = self._query_all(
            """
            SELECT id, session_id, ts_start, ts_end, run_number, total_runs,
                   status, mean_confidence, duration_ms
            FROM pipeline_runs
            ORDER BY ts_start DESC
            LIMIT 25
            """
        )

        agents = self._query_all(
            """
            SELECT agent_name, invocation_count, mean_confidence, mean_tokens,
                   tokens_in_total, tokens_out_total, error_count, last_seen
            FROM agent_stats
            ORDER BY invocation_count DESC
            """
        )

        golden = self._query_all(
            """
            SELECT task_id, category, pass, latency_ms, tokens_total, model, ts
            FROM golden_results
            ORDER BY ts DESC
            LIMIT 100
            """
        )

        anomalies = self._query_all(
            """
            SELECT ts, kind, severity, message, resolved
            FROM anomaly_events
            WHERE resolved = 0
            ORDER BY ts DESC
            LIMIT 50
            """
        )

        payload: dict[str, Any] = {
            "generated_at": _now_iso(),
            "mean_confidence_7d": round(mean_conf, 2),
            "opus_sonnet_share": share,
            "token_spend_30d": spend,
            "daily_rollups": [dict(r) for r in daily],
            "pipeline_runs": [dict(r) for r in runs],
            "agent_stats": [dict(r) for r in agents],
            "golden_results": [dict(r) for r in golden],
            "anomalies": [dict(r) for r in anomalies],
        }
        out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return payload


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Telemetry rollup CLI for opencode-framework."
    )
    p.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite db path")
    p.add_argument("--schema", default=DEFAULT_SCHEMA_PATH, help="db.sql path")
    p.add_argument("--rollup", action="store_true", help="Run daily rollup")
    p.add_argument("--date", default=None, help="Rollup date (YYYY-MM-DD)")
    p.add_argument("--anomalies", action="store_true", help="Detect anomalies")
    p.add_argument(
        "--export",
        default=None,
        help="Export dashboard JSON to path (e.g. telemetry/dashboard/data/rollup.json)",
    )
    p.add_argument("--apply-schema", action="store_true", help="Apply db.sql")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rollup = TelemetryRollup(db_path=args.db, schema_path=args.schema)
    try:
        if args.apply_schema or args.rollup or args.export or args.anomalies:
            rollup.apply_schema()

        if args.rollup:
            rec = rollup.run_rollup(args.date)
            print(json.dumps({"rollup": rec}, indent=2, default=str))

        if args.anomalies:
            anomalies = rollup.detect_anomalies()
            print(json.dumps({"anomalies": anomalies}, indent=2))

        if args.export:
            payload = rollup.export_for_dashboard(args.export)
            print(
                json.dumps(
                    {
                        "exported": args.export,
                        "size_bytes": os.path.getsize(args.export),
                        "mean_confidence_7d": payload["mean_confidence_7d"],
                    },
                    indent=2,
                )
            )

        if not (args.apply_schema or args.rollup or args.export or args.anomalies):
            _build_arg_parser().print_help()
            return 1
    finally:
        rollup.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
