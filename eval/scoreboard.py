#!/usr/bin/env python3
"""Scoreboard for the opencode golden suite.

Reads the latest results JSONL from eval/results and the telemetry
SQLite database, then prints a color coded terminal summary, writes a
markdown scoreboard, and optionally merges the latest golden results
into the dashboard rollup JSON.

Zero banned dashes. ASCII hyphen only.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_RESULTS_PATH = "eval/results/results_latest.jsonl"
DEFAULT_TELEMETRY_DB = ".claude/hooks/logs/telemetry.sqlite"
DEFAULT_REPORT_PATH = "eval/results/scoreboard.md"
DEFAULT_DASHBOARD_DATA = "telemetry/dashboard/data/rollup.json"

# ANSI color codes, gated by stdout isatty.
_USE_COLOR = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"

def _green(s: str) -> str: return _c("32", s)
def _yellow(s: str) -> str: return _c("33", s)
def _red(s: str) -> str:   return _c("31", s)
def _bold(s: str) -> str:  return _c("1",  s)
def _dim(s: str) -> str:   return _c("2",  s)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return float(ordered[k])


class Scoreboard:
    """Compute pass rate, latency, token spend and write reports."""

    def __init__(
        self,
        results_path: str = DEFAULT_RESULTS_PATH,
        telemetry_db: str = DEFAULT_TELEMETRY_DB,
    ) -> None:
        self.results_path = results_path
        self.telemetry_db = telemetry_db
        self.results: list[dict[str, Any]] = self._load_results(results_path)

    def _load_results(self, path: str) -> list[dict[str, Any]]:
        p = Path(path)
        if not p.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    # -- metrics --------------------------------------------------------

    def compute_pass_rate(self) -> float:
        if not self.results:
            return 0.0
        passed = sum(1 for r in self.results if r.get("pass"))
        return round(passed / len(self.results) * 100.0, 2)

    def compute_latency_p95(self) -> float:
        values = [float(r.get("latency_ms") or 0) for r in self.results]
        return round(_percentile(values, 95.0), 2)

    def compute_category_breakdown(self) -> dict[str, dict[str, Any]]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in self.results:
            groups[r.get("category", "unknown")].append(r)
        out: dict[str, dict[str, Any]] = {}
        for cat, rows in groups.items():
            passed = sum(1 for r in rows if r.get("pass"))
            latencies = [float(r.get("latency_ms") or 0) for r in rows]
            tokens = [int(r.get("tokens") or 0) for r in rows]
            out[cat] = {
                "count": len(rows),
                "pass": passed,
                "pass_rate_pct": round(passed / len(rows) * 100.0, 2) if rows else 0.0,
                "p95_latency_ms": round(_percentile(latencies, 95.0), 2),
                "mean_tokens": round(statistics.fmean(tokens), 1) if tokens else 0.0,
            }
        return out

    def compute_token_spend_report(self) -> dict[str, Any]:
        opus_tokens = 0
        sonnet_tokens = 0
        for r in self.results:
            model = r.get("model") or ""
            tokens = int(r.get("tokens") or 0)
            if model.startswith("claude-opus"):
                opus_tokens += tokens
            elif model.startswith("claude-sonnet"):
                sonnet_tokens += tokens
        # Rough blended cost assuming average of in/out mix.
        cost_opus = opus_tokens * 45.0 / 1_000_000.0
        cost_sonnet = sonnet_tokens * 9.0 / 1_000_000.0
        return {
            "opus_tokens": opus_tokens,
            "sonnet_tokens": sonnet_tokens,
            "total_tokens": opus_tokens + sonnet_tokens,
            "estimated_cost_usd": round(cost_opus + cost_sonnet, 4),
            "opus_share_pct": round(
                (opus_tokens / (opus_tokens + sonnet_tokens) * 100.0)
                if (opus_tokens + sonnet_tokens) > 0
                else 0.0,
                2,
            ),
        }

    # -- reporting ------------------------------------------------------

    def print_terminal(self) -> None:
        total = len(self.results)
        rate = self.compute_pass_rate()
        p95 = self.compute_latency_p95()
        spend = self.compute_token_spend_report()

        print(_bold("opencode golden scoreboard"))
        print(_dim(f"results: {os.path.abspath(self.results_path)}"))
        print(_dim(f"generated_at: {_now_iso()}"))
        print()

        rate_str = f"{rate:.2f}%"
        if rate >= 95:
            rate_str = _green(rate_str)
        elif rate >= 85:
            rate_str = _yellow(rate_str)
        else:
            rate_str = _red(rate_str)
        print(f"  pass rate: {rate_str}   tasks: {total}")
        print(f"  p95 latency: {p95:.0f} ms")
        print(
            f"  tokens: total {spend['total_tokens']}  opus {spend['opus_tokens']}  "
            f"sonnet {spend['sonnet_tokens']}  opus_share {spend['opus_share_pct']}%"
        )
        print(f"  estimated cost: ${spend['estimated_cost_usd']:.4f}")
        print()

        print(_bold("per category"))
        print(f"  {'category':<22} {'count':>5} {'pass':>5} {'rate':>7} {'p95_ms':>8} {'mean_tok':>10}")
        for cat, row in sorted(self.compute_category_breakdown().items()):
            rate_cat = f"{row['pass_rate_pct']:.1f}%"
            if row["pass_rate_pct"] >= 95:
                rate_cat = _green(rate_cat)
            elif row["pass_rate_pct"] >= 85:
                rate_cat = _yellow(rate_cat)
            else:
                rate_cat = _red(rate_cat)
            print(
                f"  {cat:<22} {row['count']:>5} {row['pass']:>5} {rate_cat:>13} "
                f"{row['p95_latency_ms']:>8.0f} {row['mean_tokens']:>10.0f}"
            )
        print()

        anomalies = self._load_anomalies()
        if anomalies:
            print(_bold(_red("anomalies")))
            for a in anomalies[:10]:
                print(f"  [{a['kind']}] {a['message']}")
        else:
            print(_dim("no active anomalies"))

    def generate_markdown_report(self, out_path: str = DEFAULT_REPORT_PATH) -> str:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        rate = self.compute_pass_rate()
        p95 = self.compute_latency_p95()
        spend = self.compute_token_spend_report()
        cats = self.compute_category_breakdown()
        anomalies = self._load_anomalies()

        lines: list[str] = []
        lines.append("# Opencode Golden Scoreboard")
        lines.append("")
        lines.append(f"Generated: {_now_iso()}")
        lines.append(f"Results file: `{self.results_path}`")
        lines.append(f"Total tasks: {len(self.results)}")
        lines.append("")
        lines.append("## Headline")
        lines.append("")
        lines.append(f"- Pass rate: **{rate:.2f}%**")
        lines.append(f"- p95 latency: **{p95:.0f} ms**")
        lines.append(f"- Total tokens: **{spend['total_tokens']}**")
        lines.append(f"- Opus share: **{spend['opus_share_pct']:.2f}%**")
        lines.append(f"- Estimated cost: **${spend['estimated_cost_usd']:.4f}**")
        lines.append("")
        lines.append("## Per Category")
        lines.append("")
        lines.append("| Category | Count | Pass | Rate | p95 ms | Mean tokens |")
        lines.append("|----------|------:|-----:|-----:|-------:|------------:|")
        for cat, row in sorted(cats.items()):
            lines.append(
                f"| {cat} | {row['count']} | {row['pass']} | {row['pass_rate_pct']:.1f}% | "
                f"{row['p95_latency_ms']:.0f} | {row['mean_tokens']:.0f} |"
            )
        lines.append("")
        lines.append("## Anomalies")
        lines.append("")
        if anomalies:
            for a in anomalies:
                lines.append(f"- **{a['kind']}**: {a['message']} ({a['ts']})")
        else:
            lines.append("- None")
        lines.append("")
        Path(out_path).write_text("\n".join(lines), encoding="utf-8")
        return out_path

    def push_to_dashboard(self, dashboard_data_path: str = DEFAULT_DASHBOARD_DATA) -> None:
        path = Path(dashboard_data_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {}
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
        payload["generated_at"] = _now_iso()
        payload["golden_results"] = [
            {
                "task_id": r.get("task_id"),
                "category": r.get("category"),
                "pass": 1 if r.get("pass") else 0,
                "latency_ms": int(r.get("latency_ms") or 0),
                "tokens_total": int(r.get("tokens") or 0),
                "model": r.get("model") or "unknown",
                "ts": r.get("ts") or _now_iso(),
            }
            for r in self.results
        ]
        payload["golden_summary"] = {
            "pass_rate_pct": self.compute_pass_rate(),
            "p95_latency_ms": self.compute_latency_p95(),
            "token_spend": self.compute_token_spend_report(),
            "categories": self.compute_category_breakdown(),
        }
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def _load_anomalies(self) -> list[dict[str, Any]]:
        db = Path(self.telemetry_db)
        if not db.exists():
            return []
        try:
            conn = sqlite3.connect(str(db))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT ts, kind, severity, message FROM anomaly_events "
                "WHERE resolved = 0 ORDER BY ts DESC LIMIT 25"
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except sqlite3.Error:
            return []


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Golden suite scoreboard.")
    p.add_argument("--results", default=DEFAULT_RESULTS_PATH)
    p.add_argument("--db", default=DEFAULT_TELEMETRY_DB)
    p.add_argument("--report", default=DEFAULT_REPORT_PATH)
    p.add_argument("--dashboard-data", default=DEFAULT_DASHBOARD_DATA)
    p.add_argument("--print", action="store_true", help="Print terminal summary")
    p.add_argument("--write-report", action="store_true", help="Write markdown report")
    p.add_argument("--push-dashboard", action="store_true", help="Merge into rollup.json")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    sb = Scoreboard(results_path=args.results, telemetry_db=args.db)
    did = False
    if args.print:
        sb.print_terminal()
        did = True
    if args.write_report:
        path = sb.generate_markdown_report(args.report)
        print(f"wrote {path}")
        did = True
    if args.push_dashboard:
        sb.push_to_dashboard(args.dashboard_data)
        print(f"updated {args.dashboard_data}")
        did = True
    if not did:
        sb.print_terminal()
    return 0


if __name__ == "__main__":
    sys.exit(main())
