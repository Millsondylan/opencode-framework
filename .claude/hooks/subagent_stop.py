#!/usr/bin/env python3
"""
SubagentStop hook for Claude Code.

Runs when a pipeline subagent (Task tool) completes. Five responsibilities:

1. Parse stdin JSON (fields subagent_type, output/result, session_id,
   exit_code). Non pipeline subagents are approved as a no op.
2. Filter: only act on pipeline roles (plan-agent, decide-agent,
   review-agent, build-agent-*, debugger*, pipeline-scaler,
   task-breakdown, code-discovery, docs-researcher,
   pre-flight-checker, test-writer, logical-agent, test-agent,
   integration-agent). Wildcards match by prefix.
3. Decision record append: write a Michael Nygard ADR lite entry to
   docs/decisions/YYYY-MM-DD.md (today, UTC) following the canonical
   entry format defined at the head of the file. Create the file with
   a minimal header if it does not yet exist.
4. Telemetry log: insert a subagent_stopped event into
   .claude/hooks/logs/telemetry.sqlite. Creates the subagent_events
   table on demand alongside the tool_events and stop_events tables
   written by the other hooks.
5. Emit hookSpecificOutput so the orchestrator sees the audit trail
   path. SubagentStop hooks never block; exit 0 always.

Protocol: reads JSON on stdin, writes one JSON object to stdout of the
form {"hookSpecificOutput": {"hookEventName":"SubagentStop",
"additionalContext":"..."}}. Every exception path falls back to a
silent approve.

Self contained: Python 3 stdlib only. Source contains zero literal em
dash, en dash, figure dash, or horizontal bar glyphs; any reference to
the banned dash class is constructed via chr(0x20XX) at runtime per
rule 08.

Claude Code hooks reference: https://code.claude.com/docs/en/hooks
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# Paths. subagent_stop lives in .claude/hooks next to the other Python
# hooks; docs/decisions is two levels up at the repository root.
HOOK_DIR = Path(__file__).resolve().parent
LOG_DIR = HOOK_DIR / "logs"
DB_PATH = LOG_DIR / "telemetry.sqlite"
REPO_ROOT = HOOK_DIR.parent.parent
DECISIONS_DIR = REPO_ROOT / "docs" / "decisions"

# How many characters of the subagent output to capture in the decision
# record Decision field. The full output is archived in telemetry.
DECISION_OUTPUT_HEAD = 500

# How many characters of the output to keep in the telemetry row.
TELEMETRY_OUTPUT_HEAD = 2048

# Banned dash class, built from escape codes so this file itself stays
# ASCII clean. U+2014 EM DASH, U+2013 EN DASH, U+2012 FIGURE DASH,
# U+2015 HORIZONTAL BAR. Any of these present in subagent output are
# replaced with a plain ASCII hyphen before the record is written.
_BANNED_DASHES = (chr(0x2014), chr(0x2013), chr(0x2012), chr(0x2015))

# Pipeline subagent roles. Prefix entries marked with a trailing star
# match by prefix (build-agent-1, build-agent-55, debugger-2, etc.).
PIPELINE_EXACT = frozenset(
    {
        "plan-agent",
        "decide-agent",
        "review-agent",
        "pipeline-scaler",
        "task-breakdown",
        "code-discovery",
        "docs-researcher",
        "pre-flight-checker",
        "test-writer",
        "logical-agent",
        "test-agent",
        "integration-agent",
    }
)
PIPELINE_PREFIXES = (
    "build-agent-",
    "build-agent",
    "debugger",
)


def is_pipeline_subagent(subagent_type: str) -> bool:
    """Return True when the subagent name belongs to the mandatory pipeline."""
    if not subagent_type:
        return False
    name = subagent_type.strip()
    if name in PIPELINE_EXACT:
        return True
    # Prefix match for build-agent-N and debugger-N style names. Accept
    # the bare 'debugger' and 'build-agent' as well so the first links
    # of the chains count as pipeline work.
    for prefix in PIPELINE_PREFIXES:
        if name == prefix or name.startswith(prefix):
            return True
    return False


def strip_banned_dashes(text: str) -> str:
    """Replace banned Unicode dashes with ASCII hyphens per rule 08."""
    if not text:
        return ""
    out = text
    for glyph in _BANNED_DASHES:
        if glyph in out:
            out = out.replace(glyph, "-")
    return out


def ensure_db() -> Optional[sqlite3.Connection]:
    """Open telemetry.sqlite and ensure subagent_events exists.

    Returns None on any IO error. Every caller must tolerate the None
    case since telemetry is best effort and must never block the hook.
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=0.5)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subagent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                session_id TEXT,
                subagent_type TEXT NOT NULL,
                exit_code INTEGER,
                output_head TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_subagent_events_session_ts "
            "ON subagent_events(session_id, ts)"
        )
        conn.commit()
        return conn
    except Exception:
        return None


def log_subagent(
    conn: Optional[sqlite3.Connection],
    session_id: str,
    subagent_type: str,
    exit_code: Optional[int],
    output_head: str,
) -> None:
    """Insert a subagent_stopped row. Never raises."""
    if conn is None:
        return
    try:
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO subagent_events(
                ts, session_id, subagent_type, exit_code, output_head
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                ts,
                session_id or "",
                subagent_type or "",
                int(exit_code) if isinstance(exit_code, int) else None,
                output_head or "",
            ),
        )
        conn.commit()
    except Exception:
        return


def _extract_output(data: dict) -> str:
    """Best effort extraction of the subagent textual output.

    Accepts either a top level `output` string, a `result` string, or a
    nested dict that carries one of the common fields (output, text,
    content, message). Returns an empty string when nothing is found.
    """
    for key in ("output", "result", "text", "content", "message"):
        val = data.get(key)
        if isinstance(val, str) and val:
            return val
    # Nested shapes: Task tool historically wraps output under
    # tool_response or hook_input depending on runtime version.
    for outer in ("tool_response", "hook_input", "payload", "response"):
        block = data.get(outer)
        if isinstance(block, dict):
            for key in ("output", "result", "text", "content", "message"):
                val = block.get(key)
                if isinstance(val, str) and val:
                    return val
    return ""


def _extract_exit_code(data: dict) -> Optional[int]:
    """Best effort exit code extraction. Returns None when unknown."""
    for key in ("exit_code", "exitCode", "exit_status", "status"):
        val = data.get(key)
        if isinstance(val, int):
            return val
    tr = data.get("tool_response")
    if isinstance(tr, dict):
        for key in ("exit_code", "exitCode", "exit_status", "status"):
            val = tr.get(key)
            if isinstance(val, int):
                return val
        if tr.get("error"):
            return 1
        success = tr.get("success")
        if isinstance(success, bool):
            return 0 if success else 1
    return None


def append_decision_record(
    subagent_type: str,
    session_id: str,
    exit_code: Optional[int],
    output: str,
) -> Path:
    """Append a canonical entry to docs/decisions/YYYY-MM-DD.md.

    Returns the path that was written to. On any IO error the function
    still returns the path it attempted so the caller can surface it in
    additionalContext; errors are swallowed to preserve the never block
    contract of SubagentStop hooks.
    """
    now = datetime.now(timezone.utc)
    date_slug = now.strftime("%Y-%m-%d")
    ts_slug = now.strftime("%Y-%m-%dT%H:%M:%S")
    target = DECISIONS_DIR / f"{date_slug}.md"

    exit_repr = int(exit_code) if isinstance(exit_code, int) else 0

    cleaned = strip_banned_dashes(output or "")
    decision_head = cleaned[:DECISION_OUTPUT_HEAD].strip()
    if not decision_head:
        decision_head = "Subagent produced no textual output."

    context = (
        f"subagent_stop hook captured completion of {subagent_type}"
    )
    rationale = (
        "Captured for pipeline audit trail per operating rule 7."
    )
    related = f"session_id: {session_id or 'unknown'}"

    entry_lines = [
        "",
        f"## [{ts_slug}] {subagent_type} (exit {exit_repr})",
        "",
        "### Context",
        context,
        "",
        "### Decision",
        decision_head,
        "",
        "### Rationale",
        rationale,
        "",
        "### Related",
        related,
        "",
    ]
    entry = "\n".join(entry_lines)

    try:
        DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
        header_exists = target.is_file()
        if not header_exists:
            header = (
                f"# Decision Records: {date_slug}\n"
                "\n"
                "This file is appended by the subagent_stop hook after each "
                "pipeline subagent completes.\n"
            )
            with target.open("w", encoding="utf-8") as fh:
                fh.write(header)
                fh.write(entry)
        else:
            with target.open("a", encoding="utf-8") as fh:
                fh.write(entry)
    except Exception:
        # Best effort: never raise, never block the hook.
        return target
    return target


def _emit(additional_context: str) -> int:
    """Emit SubagentStop approval.

    Claude Code's SubagentStop event schema does NOT accept
    hookSpecificOutput. Only PreToolUse, UserPromptSubmit, PostToolUse,
    and PostToolBatch accept that field. For SubagentStop we emit a
    minimal {"continue": true} payload and route the audit trail context
    to stderr (visible in operator logs) plus the telemetry sqlite DB.
    """
    if additional_context:
        try:
            sys.stderr.write(additional_context + "\n")
        except Exception:
            pass
    try:
        print(json.dumps({"continue": True}))
    except Exception:
        print('{"continue":true}')
    return 0


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return _emit("subagent_stop: malformed stdin, approving")

    if not isinstance(data, dict):
        return _emit("subagent_stop: non-object payload, approving")

    subagent_type = str(data.get("subagent_type") or "").strip()
    session_id = str(data.get("session_id") or "")

    # Filter: only pipeline roles trigger the audit trail work.
    if not is_pipeline_subagent(subagent_type):
        return _emit(
            f"subagent_stop: non pipeline subagent '{subagent_type}', no op"
        )

    output = _extract_output(data)
    exit_code = _extract_exit_code(data)

    # Decision record append.
    try:
        record_path = append_decision_record(
            subagent_type=subagent_type,
            session_id=session_id,
            exit_code=exit_code,
            output=output,
        )
        record_path_str = str(record_path)
    except Exception:
        record_path_str = ""

    # Telemetry log.
    conn = ensure_db()
    try:
        head = strip_banned_dashes(output or "")[:TELEMETRY_OUTPUT_HEAD]
        log_subagent(
            conn=conn,
            session_id=session_id,
            subagent_type=subagent_type,
            exit_code=exit_code,
            output_head=head,
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    if record_path_str:
        context = f"decision record appended: {record_path_str}"
    else:
        context = "decision record append failed silently"
    return _emit(context)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Final silent approve guard: SubagentStop must never crash the pipeline.
        try:
            print('{"continue":true}')
        except Exception:
            pass
        sys.exit(0)
