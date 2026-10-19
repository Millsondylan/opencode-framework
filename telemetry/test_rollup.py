#!/usr/bin/env python3
"""Tests for telemetry/rollup.py.

Run: python3 telemetry/test_rollup.py

Uses a temporary SQLite file per test, populates it with synthetic
agent_invocations rows, and exercises each rollup method. Reports
pass or fail per test with a summary. Zero banned dashes.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make telemetry module importable when invoked directly.
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

from telemetry.rollup import (  # noqa: E402
    CONFIDENCE_FLOOR,
    TelemetryRollup,
)

SCHEMA_PATH = str(HERE / "db.sql")


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _seed_invocations(rollup: TelemetryRollup, rows: list[dict]) -> None:
    rollup.conn.executemany(
        """
        INSERT INTO agent_invocations (
            ts, agent_name, stage_number, session_id, model,
            tokens_in, tokens_out, duration_ms, confidence_score,
            outcome, error
        )
        VALUES (:ts, :agent_name, :stage_number, :session_id, :model,
                :tokens_in, :tokens_out, :duration_ms, :confidence_score,
                :outcome, :error)
        """,
        rows,
    )
    rollup.conn.commit()


def _mk_rollup() -> tuple[TelemetryRollup, str]:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
    tmp.close()
    rollup = TelemetryRollup(db_path=tmp.name, schema_path=SCHEMA_PATH)
    rollup.apply_schema()
    return rollup, tmp.name


def _cleanup(rollup: TelemetryRollup, path: str) -> None:
    rollup.close()
    try:
        os.unlink(path)
    except OSError:
        pass


# -- test cases ---------------------------------------------------------

def test_schema_applies() -> None:
    rollup, path = _mk_rollup()
    try:
        tables = [
            r[0]
            for r in rollup.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        for required in [
            "agent_invocations",
            "pipeline_runs",
            "golden_results",
            "daily_rollups",
            "anomaly_events",
        ]:
            assert required in tables, f"table missing: {required} in {tables}"
        views = [
            r[0]
            for r in rollup.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
            ).fetchall()
        ]
        for v in ("agent_stats", "daily_cost", "recent_runs"):
            assert v in views, f"view missing: {v} in {views}"
    finally:
        _cleanup(rollup, path)


def test_rollup_computes_mean_confidence() -> None:
    rollup, path = _mk_rollup()
    try:
        now = datetime.now(timezone.utc)
        rows = [
            {
                "ts": _iso(now - timedelta(hours=2)),
                "agent_name": "build-agent-1",
                "stage_number": 9,
                "session_id": "s1",
                "model": "claude-opus-4-7",
                "tokens_in": 1000,
                "tokens_out": 500,
                "duration_ms": 1500,
                "confidence_score": 95,
                "outcome": "ok",
                "error": None,
            },
            {
                "ts": _iso(now - timedelta(hours=1)),
                "agent_name": "review-agent",
                "stage_number": 15,
                "session_id": "s1",
                "model": "claude-sonnet-4-6",
                "tokens_in": 500,
                "tokens_out": 250,
                "duration_ms": 800,
                "confidence_score": 93,
                "outcome": "ok",
                "error": None,
            },
        ]
        _seed_invocations(rollup, rows)
        mc = rollup.compute_mean_confidence(days=1)
        assert 93.9 < mc < 94.1, f"expected ~94.0, got {mc}"

        rec = rollup.run_rollup(date=now.date().isoformat())
        assert rec["invocation_count"] == 2
        assert rec["tokens_in_total"] == 1500
        assert rec["tokens_out_total"] == 750
        assert rec["opus_count"] == 1
        assert rec["sonnet_count"] == 1
    finally:
        _cleanup(rollup, path)


def test_opus_sonnet_share_correct() -> None:
    rollup, path = _mk_rollup()
    try:
        now = datetime.now(timezone.utc)
        base = {
            "ts": _iso(now),
            "agent_name": "build-agent-1",
            "stage_number": 9,
            "session_id": "s1",
            "tokens_in": 10,
            "tokens_out": 10,
            "duration_ms": 100,
            "confidence_score": 95,
            "outcome": "ok",
            "error": None,
        }
        rows = []
        for _ in range(3):
            r = dict(base)
            r["model"] = "claude-opus-4-7"
            rows.append(r)
        for _ in range(7):
            r = dict(base)
            r["model"] = "claude-sonnet-4-6"
            rows.append(r)
        _seed_invocations(rollup, rows)

        share = rollup.compute_opus_sonnet_share()
        assert share["total"] == 10
        assert share["opus"] == 30.0, f"opus share {share['opus']}"
        assert share["sonnet"] == 70.0, f"sonnet share {share['sonnet']}"
    finally:
        _cleanup(rollup, path)


def test_token_spend_calculation() -> None:
    rollup, path = _mk_rollup()
    try:
        now = datetime.now(timezone.utc)
        rows = [
            {
                "ts": _iso(now - timedelta(days=1)),
                "agent_name": "plan-agent",
                "stage_number": 6,
                "session_id": "s1",
                "model": "claude-opus-4-7",
                "tokens_in": 1_000_000,
                "tokens_out": 500_000,
                "duration_ms": 2000,
                "confidence_score": 96,
                "outcome": "ok",
                "error": None,
            },
            {
                "ts": _iso(now - timedelta(days=2)),
                "agent_name": "code-discovery",
                "stage_number": 5,
                "session_id": "s1",
                "model": "claude-sonnet-4-6",
                "tokens_in": 2_000_000,
                "tokens_out": 1_000_000,
                "duration_ms": 1500,
                "confidence_score": 94,
                "outcome": "ok",
                "error": None,
            },
        ]
        _seed_invocations(rollup, rows)
        spend = rollup.compute_token_spend(days=30)
        assert spend["opus_tokens_in"] == 1_000_000
        assert spend["opus_tokens_out"] == 500_000
        assert spend["sonnet_tokens_in"] == 2_000_000
        assert spend["sonnet_tokens_out"] == 1_000_000
        # Cost: opus 1m in * 15 + 0.5m out * 75 + sonnet 2m in * 3 + 1m out * 15
        #     = 15 + 37.5 + 6 + 15 = 73.5
        assert abs(spend["estimated_cost_usd"] - 73.5) < 0.01, spend["estimated_cost_usd"]
    finally:
        _cleanup(rollup, path)


def test_anomaly_detection_low_confidence() -> None:
    rollup, path = _mk_rollup()
    try:
        now = datetime.now(timezone.utc)
        rows = [
            {
                "ts": _iso(now - timedelta(hours=i)),
                "agent_name": "build-agent-1",
                "stage_number": 9,
                "session_id": "s1",
                "model": "claude-sonnet-4-6",
                "tokens_in": 100,
                "tokens_out": 50,
                "duration_ms": 500,
                "confidence_score": 80,
                "outcome": "ok",
                "error": None,
            }
            for i in range(1, 12)
        ]
        _seed_invocations(rollup, rows)
        anomalies = rollup.detect_anomalies()
        joined = " | ".join(anomalies)
        assert any("low_confidence" in a for a in anomalies), (
            f"expected low_confidence anomaly given floor {CONFIDENCE_FLOOR}, got: {joined}"
        )

        logged = rollup.conn.execute(
            "SELECT kind FROM anomaly_events"
        ).fetchall()
        assert any(row[0] == "low_confidence" for row in logged), "anomaly not logged"
    finally:
        _cleanup(rollup, path)


def test_export_for_dashboard_writes_json() -> None:
    rollup, path = _mk_rollup()
    try:
        now = datetime.now(timezone.utc)
        rows = [
            {
                "ts": _iso(now),
                "agent_name": "build-agent-1",
                "stage_number": 9,
                "session_id": "s1",
                "model": "claude-opus-4-7",
                "tokens_in": 10,
                "tokens_out": 5,
                "duration_ms": 100,
                "confidence_score": 97,
                "outcome": "ok",
                "error": None,
            }
        ]
        _seed_invocations(rollup, rows)
        rollup.run_rollup()

        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "rollup.json")
            payload = rollup.export_for_dashboard(out)
            assert os.path.exists(out), "export file not created"
            loaded = json.loads(Path(out).read_text(encoding="utf-8"))
            for key in (
                "generated_at",
                "mean_confidence_7d",
                "opus_sonnet_share",
                "token_spend_30d",
                "daily_rollups",
                "pipeline_runs",
                "agent_stats",
                "golden_results",
                "anomalies",
            ):
                assert key in loaded, f"missing key {key} in exported json"
            assert loaded["opus_sonnet_share"]["total"] == 1
            assert payload["opus_sonnet_share"]["opus"] == 100.0
    finally:
        _cleanup(rollup, path)


# -- runner -------------------------------------------------------------

TESTS = [
    test_schema_applies,
    test_rollup_computes_mean_confidence,
    test_opus_sonnet_share_correct,
    test_token_spend_calculation,
    test_anomaly_detection_low_confidence,
    test_export_for_dashboard_writes_json,
]


def main() -> int:
    passed = 0
    failed = 0
    for fn in TESTS:
        name = fn.__name__
        try:
            fn()
            passed += 1
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {exc}")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
