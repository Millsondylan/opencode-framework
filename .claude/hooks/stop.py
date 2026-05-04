#!/usr/bin/env python3
"""
Stop hook for Claude Code.

Runs when the main agent finishes a turn. Seven responsibilities:

1. Parse stdin JSON (fields stop_hook_active, transcript_path, session_id, cwd).
2. Transcript scan: if transcript_path is readable, read the last assistant
   turn and scan for banned dash glyphs and CONFIDENCE score blocks.
3. Score aggregation: collect every `Score: N/100` line across the scanned
   region and compute the arithmetic mean.
4. Multi-critic gate: production threshold 95, hackathon threshold 85
   (toggle via HACKATHON=1). Block the stop if the mean falls below the
   active threshold.
5. Dash-leak warning: never block on terminal hook; dashes surface in the
   additionalContext field and telemetry only.
6. Telemetry: append a stop event to .claude/hooks/logs/telemetry.sqlite
   including mean score and dash_leak_count.
7. Decision record append: append a short entry to docs/decisions/YYYY-MM-DD.md
   (today, UTC) describing the stop. Best effort. Must not crash on filesystem
   errors or missing parent directories.

Protocol: reads JSON on stdin, writes one JSON object to stdout. Exit 0 on
approve, exit 2 on gate failure. Never crashes: every exception path falls
back to approve or a minimal JSON emit.

Self-contained: Python 3 stdlib only. Source contains zero literal em-dash,
en-dash, figure-dash, or horizontal-bar glyphs; all references are built via
chr(0x20XX) at runtime.

Claude Code hooks reference: https://code.claude.com/docs/en/hooks
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# Paths.
HOOK_DIR = Path(__file__).resolve().parent
LOG_DIR = HOOK_DIR / "logs"
DB_PATH = LOG_DIR / "telemetry.sqlite"

# docs/decisions is two levels above .claude/hooks (repo root / docs / decisions).
REPO_ROOT = HOOK_DIR.parent.parent
DECISIONS_DIR = REPO_ROOT / "docs" / "decisions"

# Maximum bytes of the transcript tail to scan. The JSONL transcript grows
# monotonically, so scanning the full file every turn scales poorly. Cap to
# the last 256 KiB which is comfortably larger than any single turn.
TRANSCRIPT_TAIL_BYTES = 256 * 1024

# Confidence score regex per rule 09.
CONFIDENCE_RE = re.compile(r"Score:\s*(\d+)\s*/\s*100", re.IGNORECASE)

# Banned dash class. U+2014 EM, U+2013 EN, U+2012 FIGURE, U+2015 HORIZONTAL BAR.
BANNED_DASH_PATTERN = re.compile(
    "[" + chr(0x2014) + chr(0x2013) + chr(0x2012) + chr(0x2015) + "]"
)

# Thresholds: production default 95, hackathon 85 when HACKATHON=1.
THRESHOLD_PROD = 95
THRESHOLD_HACK = 85


def _active_threshold() -> int:
    if os.environ.get("HACKATHON") == "1":
        return THRESHOLD_HACK
    return THRESHOLD_PROD


def read_transcript_tail(path: str) -> str:
    """Read the last TRANSCRIPT_TAIL_BYTES of the transcript file.

    Transcript files are JSONL; we return the raw text for downstream parsers.
    Returns "" on any filesystem or decoding error.
    """
    if not path:
        return ""
    try:
        p = Path(path)
        if not p.is_file():
            return ""
        size = p.stat().st_size
        with p.open("rb") as fh:
            if size > TRANSCRIPT_TAIL_BYTES:
                fh.seek(size - TRANSCRIPT_TAIL_BYTES)
                # Advance past any partial line to keep JSONL parsing clean.
                fh.readline()
            data = fh.read()
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def extract_last_assistant_text(transcript_tail: str) -> str:
    """Return the text content of the most recent assistant turn.

    Transcripts are JSONL: one JSON object per line with a `role` field
    (`user` or `assistant`) and a `content` field that is either a string or
    a list of content blocks (Anthropic messages API style). We walk the lines
    in reverse and stop at the first assistant turn, concatenating any text
    blocks found.
    """
    if not transcript_tail:
        return ""
    lines = transcript_tail.splitlines()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        # Handle both shapes: {"role":"assistant","content":...} and
        # {"type":"message","message":{"role":"assistant","content":...}}.
        role = obj.get("role")
        content = obj.get("content")
        if role is None:
            msg = obj.get("message")
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content")
        if role != "assistant":
            continue
        return _flatten_content(content)
    return ""


def _flatten_content(content: Any) -> str:
    """Flatten a content field into plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                t = block.get("type")
                if t in (None, "text"):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                elif t == "tool_use":
                    # Skip tool-use payloads; they are not author prose.
                    continue
                elif t == "tool_result":
                    continue
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def scan_scores(text: str) -> list[int]:
    """Extract all `Score: N/100` integers from the text."""
    if not text:
        return []
    out: list[int] = []
    for m in CONFIDENCE_RE.finditer(text):
        try:
            n = int(m.group(1))
        except Exception:
            continue
        if 0 <= n <= 100:
            out.append(n)
    return out


def scan_dashes(text: str) -> int:
    if not text:
        return 0
    return len(BANNED_DASH_PATTERN.findall(text))


def mean(values: list[int]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def ensure_db() -> Optional[sqlite3.Connection]:
    """Open telemetry.sqlite and create the stop_events table. Returns None on error."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=0.5)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stop_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                session_id TEXT,
                score_count INTEGER,
                score_mean REAL,
                dash_leak_count INTEGER DEFAULT 0,
                threshold INTEGER,
                decision TEXT,
                reason TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stop_events_session_ts "
            "ON stop_events(session_id, ts)"
        )
        conn.commit()
        return conn
    except Exception:
        return None


def log_stop(
    conn: Optional[sqlite3.Connection],
    session_id: str,
    score_count: int,
    score_mean: Optional[float],
    dash_leak_count: int,
    threshold: int,
    decision: str,
    reason: str,
) -> None:
    """Append a row to stop_events. Never raises."""
    if conn is None:
        return
    try:
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO stop_events(
                ts, session_id, score_count, score_mean,
                dash_leak_count, threshold, decision, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                session_id or "",
                int(score_count),
                float(score_mean) if score_mean is not None else None,
                int(dash_leak_count),
                int(threshold),
                decision or "",
                reason or "",
            ),
        )
        conn.commit()
    except Exception:
        return


def append_decision_record(
    session_id: str,
    score_mean: Optional[float],
    score_count: int,
    dash_leak_count: int,
    decision: str,
    threshold: int,
) -> None:
    """Append a Michael-Nygard-lite entry to docs/decisions/YYYY-MM-DD.md.

    Best effort: missing parent directory triggers creation. On any IO error
    this function returns silently.
    """
    try:
        now = datetime.now(timezone.utc)
        date_slug = now.strftime("%Y-%m-%d")
        ts_slug = now.strftime("%Y-%m-%dT%H:%M:%S")
        target = DECISIONS_DIR / f"{date_slug}.md"
        DECISIONS_DIR.mkdir(parents=True, exist_ok=True)

        header_exists = target.is_file()

        mean_repr = f"{score_mean:.2f}" if score_mean is not None else "n/a"
        exit_n = 0 if decision == "approve" else 2

        context = (
            f"Stop hook fired on session {session_id or 'unknown'}. "
            f"Aggregated {score_count} CONFIDENCE score(s) from the last "
            f"assistant turn; active threshold {threshold}. "
            f"Dash leak count {dash_leak_count}."
        )
        rationale = (
            f"Multi-critic gate {'passed' if decision == 'approve' else 'failed'}: "
            f"mean {mean_repr} vs threshold {threshold}. "
            "Blocking here stops the turn per rule 09 enforcement."
            if decision != "approve"
            else (
                f"Multi-critic gate passed: mean {mean_repr} meets or exceeds "
                f"threshold {threshold}. No intervention required."
            )
        )
        decision_line = (
            f"Approve stop and release turn to user (mean={mean_repr}, N={score_count})."
            if decision == "approve"
            else (
                f"Block stop; require agent rerun (mean={mean_repr}, N={score_count}, "
                f"threshold={threshold})."
            )
        )
        related = (
            ".claude/hooks/stop.py, .claude/rules/09-confidence-scoring.md, "
            ".claude/rules/01-pipeline-orchestration.md, "
            ".claude/hooks/logs/telemetry.sqlite"
        )

        entry_lines = [
            "",
            f"## [{ts_slug}] stop-hook (exit {exit_n})",
            "",
            "### Context",
            context,
            "",
            "### Decision",
            decision_line,
            "",
            "### Rationale",
            rationale,
            "",
            "### Related",
            related,
            "",
        ]
        entry = "\n".join(entry_lines)

        # Bootstrap a minimal header if the file did not exist.
        if not header_exists:
            header = (
                f"# Decision Records: {date_slug}\n"
                "\n"
                "This file is appended by the stop hook and subagent-stop hook "
                "after each turn or subagent completes.\n"
            )
            with target.open("w", encoding="utf-8") as fh:
                fh.write(header)
                fh.write(entry)
        else:
            with target.open("a", encoding="utf-8") as fh:
                fh.write(entry)
    except Exception:
        return


def emit(
    decision: str,
    additional_context: str,
    reason: str = "",
) -> int:
    """Print the Stop hook payload and return the correct exit code.

    Claude Code's Stop event schema does NOT accept hookSpecificOutput.
    Only PreToolUse, UserPromptSubmit, PostToolUse, and PostToolBatch
    accept that field. For Stop:
    - approve: emit {"continue": true}; log summary to stderr + telemetry.
    - block: emit {"decision": "block", "reason": "..."}; exit 2.
    """
    # Surface the summary via stderr so operators can still see it in logs.
    if additional_context:
        try:
            sys.stderr.write(additional_context + "\n")
        except Exception:
            pass

    if decision == "block":
        payload: dict[str, Any] = {
            "decision": "block",
            "reason": reason or "Multi-critic gate failed.",
        }
    else:
        payload = {"continue": True}
    try:
        print(json.dumps(payload))
    except Exception:
        print('{"continue":true}')
    return 0 if decision == "approve" else 2


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return emit("approve", "stop: malformed stdin, approving")

    if not isinstance(data, dict):
        return emit("approve", "stop: non-object payload, approving")

    # Respect stop_hook_active: Claude sets this to True when already inside
    # a Stop hook loop; we approve immediately to avoid infinite recursion.
    if bool(data.get("stop_hook_active")):
        return emit("approve", "stop: stop_hook_active=true, approving")

    session_id = str(data.get("session_id") or "")
    transcript_path = data.get("transcript_path")
    transcript_path = transcript_path if isinstance(transcript_path, str) else ""

    # 2. Transcript scan.
    tail = read_transcript_tail(transcript_path)
    last_assistant = extract_last_assistant_text(tail)

    # 3. Score aggregation.
    scores = scan_scores(last_assistant)
    score_mean = mean(scores)

    # 5. Dash leak warning.
    dash_leak_count = scan_dashes(last_assistant)

    # 4. Multi-critic gate.
    threshold = _active_threshold()
    gate_fail = False
    if score_mean is not None and score_mean < threshold:
        gate_fail = True

    decision = "block" if gate_fail else "approve"
    mean_repr = f"{score_mean:.2f}" if score_mean is not None else "n/a"

    summary_parts: list[str] = []
    summary_parts.append(f"scores_found={len(scores)}")
    summary_parts.append(f"score_mean={mean_repr}")
    summary_parts.append(f"threshold={threshold}")
    summary_parts.append(f"dash_leak_count={dash_leak_count}")
    summary_parts.append(f"decision={decision}")
    if dash_leak_count > 0:
        summary_parts.append(
            "dash_warning=terminal-hook;not-blocking;please use ASCII hyphen"
        )
    summary = "stop: " + "; ".join(summary_parts)

    reason = ""
    if gate_fail:
        reason = (
            f"Multi-critic gate FAIL: mean confidence {mean_repr} "
            f"below threshold {threshold} across {len(scores)} score(s). "
            "Rerun the failing agent with an improved prompt per rule 09."
        )

    # 6. Telemetry.
    conn = ensure_db()
    try:
        log_stop(
            conn=conn,
            session_id=session_id,
            score_count=len(scores),
            score_mean=score_mean,
            dash_leak_count=dash_leak_count,
            threshold=threshold,
            decision=decision,
            reason=reason,
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # 7. Decision record append (best effort).
    append_decision_record(
        session_id=session_id,
        score_mean=score_mean,
        score_count=len(scores),
        dash_leak_count=dash_leak_count,
        decision=decision,
        threshold=threshold,
    )

    return emit(decision, summary, reason)


if __name__ == "__main__":
    sys.exit(main())
