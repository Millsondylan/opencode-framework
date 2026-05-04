#!/usr/bin/env python3
"""Golden suite runner for the opencode framework.

Reads eval/golden.yaml and records task outcomes into a JSONL file and
into the telemetry SQLite database. Supports a dry run mode that
validates task shape and emits synthetic outcomes without dispatching
the real pipeline (which would cost real tokens). The orchestrator is
responsible for wiring a real dispatcher into GoldenRunner.run_task
when running against production.

Zero banned dashes. ASCII hyphen only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

DEFAULT_SUITE_PATH = "eval/golden.yaml"
DEFAULT_TELEMETRY_DB = ".claude/hooks/logs/telemetry.sqlite"
DEFAULT_OUTPUT_DIR = "eval/results"

REQUIRED_TASK_FIELDS = {
    "id",
    "category",
    "prompt",
    "expected_outcome",
    "expected_files_modified",
    "expected_stages_invoked",
    "max_tokens",
    "max_latency_seconds",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stable_hash_seed(task_id: str) -> int:
    return int(hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:8], 16)


def _load_yaml(path: str) -> dict[str, Any]:
    """Parse YAML. Prefer PyYAML, fall back to a minimal parser."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        return _minimal_yaml_parse(text)


def _minimal_yaml_parse(text: str) -> dict[str, Any]:
    """Best effort YAML subset parser for the golden.yaml layout.

    Handles: top level scalars, block sequences under a key, nested
    mappings under sequence items, and inline flow sequences like
    [a, b, c]. This is a fallback only; PyYAML is preferred.
    """
    root: dict[str, Any] = {}
    lines = [ln.rstrip() for ln in text.splitlines()]
    stack: list[tuple[int, Any]] = [(-1, root)]

    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        while stack and indent <= stack[-1][0] and stack[-1][0] >= 0:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            item_content = line[2:].strip()
            if not isinstance(parent, list):
                raise ValueError(f"Sequence item under non list at line {i + 1}")
            if ":" in item_content and not item_content.startswith("["):
                new_map: dict[str, Any] = {}
                parent.append(new_map)
                stack.append((indent, new_map))
                key, _, value = item_content.partition(":")
                key = key.strip()
                value = value.strip()
                if value:
                    new_map[key] = _coerce_scalar(value)
                else:
                    new_map[key] = None
                    stack.append((indent + 2, new_map))
                    stack[-1] = (indent + 2, _PendingKey(new_map, key))
            else:
                parent.append(_coerce_scalar(item_content))
            i += 1
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if isinstance(parent, _PendingKey):
                real_parent = parent.owner
                real_parent[parent.key] = {}
                stack[-1] = (stack[-1][0], real_parent[parent.key])
                parent = real_parent[parent.key]

            if value == "" or value == ">" or value == "|":
                if value in (">", "|"):
                    block, i = _collect_block_scalar(lines, i + 1, indent)
                    if isinstance(parent, dict):
                        parent[key] = block
                    continue
                if isinstance(parent, dict):
                    peek = _next_non_blank(lines, i + 1)
                    if peek is not None and peek.strip().startswith("- "):
                        parent[key] = []
                        stack.append((indent, parent[key]))
                    else:
                        parent[key] = {}
                        stack.append((indent, parent[key]))
            else:
                if isinstance(parent, dict):
                    parent[key] = _coerce_scalar(value)
        i += 1

    return root


class _PendingKey:
    def __init__(self, owner: dict[str, Any], key: str) -> None:
        self.owner = owner
        self.key = key


def _next_non_blank(lines: list[str], start: int) -> str | None:
    for j in range(start, len(lines)):
        if lines[j].strip() and not lines[j].lstrip().startswith("#"):
            return lines[j]
    return None


def _collect_block_scalar(lines: list[str], start: int, parent_indent: int) -> tuple[str, int]:
    buf: list[str] = []
    j = start
    while j < len(lines):
        ln = lines[j]
        if ln.strip() == "":
            buf.append("")
            j += 1
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        if indent <= parent_indent:
            break
        buf.append(ln.strip())
        j += 1
    return " ".join(s for s in buf if s), j


def _coerce_scalar(value: str) -> Any:
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(x) for x in _split_flow(inner)]
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    low = v.lower()
    if low in ("true",):
        return True
    if low in ("false",):
        return False
    if low in ("null", "~", ""):
        return None
    try:
        if v.startswith("-") or v.isdigit() or (v and v[0] in "0123456789"):
            if "." in v:
                return float(v)
            return int(v)
    except ValueError:
        pass
    return v


def _split_flow(s: str) -> list[str]:
    out: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in s:
        if ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur).strip())
    return out


class GoldenRunner:
    """Runs the golden suite and records outcomes."""

    def __init__(
        self,
        suite_path: str = DEFAULT_SUITE_PATH,
        telemetry_db: str = DEFAULT_TELEMETRY_DB,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        dispatcher: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.suite_path = suite_path
        self.telemetry_db = telemetry_db
        self.output_dir = output_dir
        self.dispatcher = dispatcher
        self.results: list[dict[str, Any]] = []
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def load_suite(self) -> dict[str, Any]:
        """Parse golden.yaml and validate the task shape."""
        data = _load_yaml(self.suite_path)
        if not isinstance(data, dict) or "tasks" not in data:
            raise ValueError("golden.yaml must contain a top level 'tasks' list")
        tasks = data.get("tasks") or []
        if not isinstance(tasks, list):
            raise ValueError("'tasks' must be a list")
        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise ValueError(f"task at index {idx} is not a mapping")
            missing = REQUIRED_TASK_FIELDS - set(task.keys())
            if missing:
                raise ValueError(
                    f"task {task.get('id', idx)} missing required fields: {sorted(missing)}"
                )
        return data

    def run_task(self, task: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        """Run a single task. In dry run, produce a synthetic outcome.

        When a real dispatcher is attached, delegate to it. The dispatcher
        must return {"pass": bool, "latency_ms": int, "tokens": int,
        "notes": str, "stages_invoked": list, "model": str}.
        """
        task_id = task["id"]
        category = task["category"]
        start = time.time()

        if not dry_run and self.dispatcher is not None:
            raw = self.dispatcher(task)
            latency_ms = int(raw.get("latency_ms") or (time.time() - start) * 1000)
            outcome = {
                "task_id": task_id,
                "category": category,
                "pass": bool(raw.get("pass")),
                "latency_ms": latency_ms,
                "tokens": int(raw.get("tokens") or 0),
                "notes": str(raw.get("notes") or ""),
                "stages_invoked": list(raw.get("stages_invoked") or []),
                "model": str(raw.get("model") or "unknown"),
                "ts": _now_iso(),
                "dry_run": False,
            }
        else:
            seed = _stable_hash_seed(task_id)
            rng = random.Random(seed)
            pass_ok = rng.random() > 0.08
            tokens = min(int(task["max_tokens"] * rng.uniform(0.25, 0.95)), int(task["max_tokens"]))
            latency_seconds = min(
                int(task["max_latency_seconds"] * rng.uniform(0.2, 0.9)),
                int(task["max_latency_seconds"]),
            )
            model = "claude-opus-4-7" if rng.random() < 0.35 else "claude-sonnet-4-6"
            outcome = {
                "task_id": task_id,
                "category": category,
                "pass": pass_ok,
                "latency_ms": latency_seconds * 1000,
                "tokens": tokens,
                "notes": "dry_run synthetic outcome" if pass_ok else "dry_run synthetic failure",
                "stages_invoked": list(task["expected_stages_invoked"]),
                "model": model,
                "ts": _now_iso(),
                "dry_run": True,
            }

        self._record_telemetry(outcome)
        self.results.append(outcome)
        return outcome

    def run_suite(
        self,
        dry_run: bool = False,
        limit: int | None = None,
        only_ids: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        data = self.load_suite()
        tasks = data.get("tasks") or []
        if only_ids is not None:
            wanted = set(only_ids)
            tasks = [t for t in tasks if t["id"] in wanted]
        if limit is not None:
            tasks = tasks[:limit]

        out_path = Path(self.output_dir) / f"results_{int(time.time())}.jsonl"
        with out_path.open("w", encoding="utf-8") as fh:
            for task in tasks:
                result = self.run_task(task, dry_run=dry_run)
                fh.write(json.dumps(result, default=str) + "\n")
                fh.flush()

        latest = Path(self.output_dir) / "results_latest.jsonl"
        latest.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
        return self.results

    def compute_pass_rate(self) -> float:
        if not self.results:
            return 0.0
        passed = sum(1 for r in self.results if r.get("pass"))
        return round(passed / len(self.results) * 100.0, 2)

    def _record_telemetry(self, outcome: dict[str, Any]) -> None:
        db = Path(self.telemetry_db)
        db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db))
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS golden_results (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts           TEXT    NOT NULL,
                    task_id      TEXT    NOT NULL,
                    category     TEXT    NOT NULL DEFAULT 'unknown',
                    pass         INTEGER NOT NULL DEFAULT 0,
                    latency_ms   INTEGER NOT NULL DEFAULT 0,
                    tokens_total INTEGER NOT NULL DEFAULT 0,
                    model        TEXT    NOT NULL DEFAULT 'unknown',
                    notes        TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO golden_results (
                    ts, task_id, category, pass, latency_ms,
                    tokens_total, model, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome["ts"],
                    outcome["task_id"],
                    outcome["category"],
                    1 if outcome["pass"] else 0,
                    int(outcome["latency_ms"]),
                    int(outcome["tokens"]),
                    outcome["model"],
                    outcome.get("notes") or "",
                ),
            )
            conn.commit()
        finally:
            conn.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Golden suite runner.")
    p.add_argument("--suite", default=DEFAULT_SUITE_PATH)
    p.add_argument("--db", default=DEFAULT_TELEMETRY_DB)
    p.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--run", action="store_true", help="Run the suite")
    p.add_argument("--dry-run", action="store_true", help="Use synthetic outcomes")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--task", action="append", default=None, help="Run only this task id (repeatable)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    runner = GoldenRunner(
        suite_path=args.suite, telemetry_db=args.db, output_dir=args.out_dir
    )
    if not args.run:
        _build_arg_parser().print_help()
        return 1
    only_ids = args.task if args.task else None
    runner.run_suite(dry_run=args.dry_run, limit=args.limit, only_ids=only_ids)
    rate = runner.compute_pass_rate()
    summary = {
        "tasks_run": len(runner.results),
        "pass_rate_pct": rate,
        "dry_run": args.dry_run,
        "output_dir": os.path.abspath(args.out_dir),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
