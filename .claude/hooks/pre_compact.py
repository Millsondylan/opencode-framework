#!/usr/bin/env python3
"""
PreCompact hook for Claude Code.

Runs immediately before Claude Code compacts the conversation transcript
to free context window. Four responsibilities:

1. Parse stdin JSON (fields session_id, transcript_path). Malformed
   input approves silently so compaction never blocks on hook errors.
2. Memory checkpoint: if `.claude/.memory/lessons.md` exists copy it to
   `.claude/hooks/logs/memory_checkpoint_<ISOstamp>.md` so the
   consolidated memory survives the transcript rewrite.
3. Telemetry export: if `.claude/hooks/logs/telemetry.sqlite` exists,
   query tool counts, blocked events, duration, and subagent
   invocation counts scoped to the current session. Persist the result
   as JSON to `.claude/hooks/logs/telemetry_checkpoint_<ISOstamp>.json`.
4. Render a markdown summary (tool counts, block events, subagent
   invocations, banned dash leak count) and inject it via
   additionalContext so the compacted transcript retains the audit
   data the pipeline depends on.

Protocol: reads JSON on stdin, writes one JSON object to stdout of the
form {"hookSpecificOutput": {"hookEventName":"PreCompact",
"additionalContext":"<markdown>"}}. Exit 0 always. Every exception
path falls back to a silent approve.

Self contained: Python 3 stdlib only. Source contains zero literal em
dash, en dash, figure dash, or horizontal bar glyphs; the banned dash
class is built via chr(0x20XX) at runtime per rule 08.

Claude Code hooks reference: https://code.claude.com/docs/en/hooks
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# Paths. The hook lives at .claude/hooks/pre_compact.py next to the
# other Python hooks. The memory file and telemetry database are
# sibling artifacts created by other hooks and subagents.
HOOK_DIR = Path(__file__).resolve().parent
LOG_DIR = HOOK_DIR / "logs"
DB_PATH = LOG_DIR / "telemetry.sqlite"
REPO_ROOT = HOOK_DIR.parent.parent
MEMORY_DIR = HOOK_DIR.parent / ".memory"
LESSONS_PATH = MEMORY_DIR / "lessons.md"

# Banned dash glyphs, constructed from escape codes so this file itself
# remains ASCII clean. U+2014 EM, U+2013 EN, U+2012 FIGURE, U+2015
# HORIZONTAL BAR. The summary counts every occurrence found in recent
# tool events so the orchestrator can react to rule 08 drift.
_BANNED_DASHES = (chr(0x2014), chr(0x2013), chr(0x2012), chr(0x2015))


def _iso_stamp() -> str:
    """UTC ISO 8601 stamp safe for use in filenames."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def memory_checkpoint(stamp: str) -> Optional[Path]:
    """Copy lessons.md to logs/ under a timestamped filename.

    Returns the destination path on success, or None when the source
    does not exist or the copy fails. Logs are best effort.
    """
    try:
        if not LESSONS_PATH.is_file():
            return None
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        dest = LOG_DIR / f"memory_checkpoint_{stamp}.md"
        shutil.copy2(str(LESSONS_PATH), str(dest))
        return dest
    except Exception:
        return None


def _count_dash_leaks(conn: sqlite3.Connection, session_id: str) -> int:
    """Count banned dash occurrences across recent tool payloads.

    Scans the payload_preview column of tool_events for the current
    session. Each occurrence of any banned dash increments the counter
    so the summary surfaces drift even when stop.py missed it.
    """
    total = 0
    try:
        cur = conn.execute(
            "SELECT payload_preview FROM tool_events WHERE session_id = ?",
            (session_id or "",),
        )
        for (payload,) in cur.fetchall():
            if not isinstance(payload, str) or not payload:
                continue
            for glyph in _BANNED_DASHES:
                if glyph in payload:
                    total += payload.count(glyph)
    except Exception:
        return total
    return total


def telemetry_export(
    session_id: str, stamp: str
) -> tuple[Optional[Path], dict]:
    """Query telemetry.sqlite and persist a JSON snapshot.

    Returns (destination_path_or_None, summary_dict). The summary
    dictionary is always populated (possibly with empty lists) so the
    caller can render the markdown summary without another guard.
    """
    summary: dict[str, Any] = {
        "session_id": session_id or "",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool_events": [],
        "subagent_events": [],
        "dash_leak_count": 0,
        "totals": {
            "tool_invocations": 0,
            "tool_blocks": 0,
            "subagent_invocations": 0,
        },
    }
    if not DB_PATH.is_file():
        return None, summary

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=0.5)
        try:
            cur = conn.execute(
                """
                SELECT tool_name,
                       COUNT(*) AS cnt,
                       SUM(COALESCE(blocked, 0)) AS blocks,
                       AVG(COALESCE(duration_ms, 0)) AS avg_ms
                FROM tool_events
                WHERE session_id = ?
                GROUP BY tool_name
                ORDER BY cnt DESC
                """,
                (session_id or "",),
            )
            for name, cnt, blocks, avg_ms in cur.fetchall():
                row = {
                    "tool_name": name or "",
                    "count": int(cnt or 0),
                    "blocks": int(blocks or 0),
                    "avg_duration_ms": (
                        float(avg_ms) if avg_ms is not None else 0.0
                    ),
                }
                summary["tool_events"].append(row)
                summary["totals"]["tool_invocations"] += row["count"]
                summary["totals"]["tool_blocks"] += row["blocks"]
        except sqlite3.Error:
            # tool_events table may not exist yet (first session ever).
            pass

        try:
            cur = conn.execute(
                """
                SELECT subagent_type, COUNT(*) AS cnt
                FROM subagent_events
                WHERE session_id = ?
                GROUP BY subagent_type
                ORDER BY cnt DESC
                """,
                (session_id or "",),
            )
            for name, cnt in cur.fetchall():
                row = {
                    "subagent_type": name or "",
                    "count": int(cnt or 0),
                }
                summary["subagent_events"].append(row)
                summary["totals"]["subagent_invocations"] += row["count"]
        except sqlite3.Error:
            # subagent_events table may not exist when no pipeline
            # subagent has completed yet.
            pass

        summary["dash_leak_count"] = _count_dash_leaks(conn, session_id)
    except Exception:
        return None, summary
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    dest: Optional[Path] = None
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        dest = LOG_DIR / f"telemetry_checkpoint_{stamp}.json"
        with dest.open("w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, sort_keys=True)
    except Exception:
        dest = None
    return dest, summary


def render_markdown_summary(
    session_id: str,
    stamp: str,
    summary: dict,
    memory_dest: Optional[Path],
    telemetry_dest: Optional[Path],
) -> str:
    """Build the markdown summary injected into additionalContext."""
    lines: list[str] = []
    lines.append(f"## PreCompact Checkpoint {stamp}")
    lines.append("")
    lines.append(f"- session_id: {session_id or 'unknown'}")
    totals = summary.get("totals", {}) if isinstance(summary, dict) else {}
    tool_count = int(totals.get("tool_invocations", 0))
    block_count = int(totals.get("tool_blocks", 0))
    sub_count = int(totals.get("subagent_invocations", 0))
    dash_count = int(summary.get("dash_leak_count", 0))
    lines.append(f"- tool_invocations_total: {tool_count}")
    lines.append(f"- tool_blocks_total: {block_count}")
    lines.append(f"- subagent_invocations_total: {sub_count}")
    lines.append(f"- dash_leak_count: {dash_count}")
    if memory_dest is not None:
        lines.append(f"- memory_checkpoint: {memory_dest}")
    else:
        lines.append("- memory_checkpoint: absent (lessons.md not present)")
    if telemetry_dest is not None:
        lines.append(f"- telemetry_checkpoint: {telemetry_dest}")
    else:
        lines.append(
            "- telemetry_checkpoint: absent (telemetry.sqlite missing or error)"
        )

    tool_rows = summary.get("tool_events") or []
    if tool_rows:
        lines.append("")
        lines.append("### Tool counts")
        for row in tool_rows:
            if not isinstance(row, dict):
                continue
            name = row.get("tool_name") or "(unknown)"
            cnt = int(row.get("count") or 0)
            blocks = int(row.get("blocks") or 0)
            avg_ms = float(row.get("avg_duration_ms") or 0.0)
            lines.append(
                f"- {name}: count={cnt}, blocks={blocks}, avg_ms={avg_ms:.2f}"
            )

    sub_rows = summary.get("subagent_events") or []
    if sub_rows:
        lines.append("")
        lines.append("### Subagent invocations")
        for row in sub_rows:
            if not isinstance(row, dict):
                continue
            name = row.get("subagent_type") or "(unknown)"
            cnt = int(row.get("count") or 0)
            lines.append(f"- {name}: count={cnt}")

    return "\n".join(lines)


def _emit(additional_context: str) -> int:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": additional_context or "",
        }
    }
    try:
        print(json.dumps(payload))
    except Exception:
        print(
            '{"hookSpecificOutput":{"hookEventName":"PreCompact",'
            '"additionalContext":""}}'
        )
    return 0


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return _emit("pre_compact: malformed stdin, approving")

    if not isinstance(data, dict):
        return _emit("pre_compact: non-object payload, approving")

    session_id = str(data.get("session_id") or "")
    # transcript_path is accepted but not currently consumed. Keeping
    # the field read in case a future iteration wants to include a
    # transcript tail excerpt in the summary.
    _ = data.get("transcript_path")

    stamp = _iso_stamp()

    memory_dest: Optional[Path] = None
    try:
        memory_dest = memory_checkpoint(stamp)
    except Exception:
        memory_dest = None

    telemetry_dest: Optional[Path] = None
    summary: dict = {
        "session_id": session_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool_events": [],
        "subagent_events": [],
        "dash_leak_count": 0,
        "totals": {
            "tool_invocations": 0,
            "tool_blocks": 0,
            "subagent_invocations": 0,
        },
    }
    try:
        telemetry_dest, summary = telemetry_export(session_id, stamp)
    except Exception:
        telemetry_dest = None

    try:
        markdown = render_markdown_summary(
            session_id=session_id,
            stamp=stamp,
            summary=summary,
            memory_dest=memory_dest,
            telemetry_dest=telemetry_dest,
        )
    except Exception:
        markdown = f"PreCompact checkpoint {stamp}: summary render failed."

    return _emit(markdown)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Final silent approve guard: PreCompact must never block compaction.
        try:
            print(
                '{"hookSpecificOutput":{"hookEventName":"PreCompact",'
                '"additionalContext":"pre_compact: unexpected error, approving"}}'
            )
        except Exception:
            pass
        sys.exit(0)
