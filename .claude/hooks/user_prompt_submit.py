#!/usr/bin/env python3
"""
UserPromptSubmit hook for Claude Code.

Runs before each user prompt is submitted to the model. Three responsibilities:

1. Dash scan: scan the prompt for banned dash glyphs (U+2014 em, U+2013 en,
   U+2012 figure, U+2015 horizontal bar). Report count and first position to
   additionalContext so the assistant can advise the user, but do NOT block.
   User prompts routinely contain dashes and blocking would be abusive.

2. Intent classification: scan lowercase prompt for routing signals. Engineering
   verbs route to pipeline-scaler. Browser/URL terms route to claude-in-chrome.
   The classification is informational; the orchestrator still decides.

3. Telemetry: best-effort INSERT into .claude/hooks/logs/telemetry.sqlite.

Protocol: reads JSON from stdin with fields prompt, session_id, cwd. Writes a
JSON object with hookSpecificOutput.additionalContext. Always exit 0 (approve);
silent-on-error approve. UserPromptSubmit that exits non-zero drops the prompt.

Self-contained: Python 3 stdlib only. Source file contains zero literal em-dash,
en-dash, figure-dash, or horizontal-bar glyphs; all banned dash glyphs are
expressed via chr(0x20XX).

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

# Preview cap for prompt payload stored in telemetry.
PAYLOAD_PREVIEW_LIMIT = 1024

# Banned dash class constructed from escape codes only. This file contains no
# literal em/en/figure/horizontal-bar glyphs.
# U+2014 EM DASH, U+2013 EN DASH, U+2012 FIGURE DASH, U+2015 HORIZONTAL BAR.
BANNED_DASH_PATTERN = re.compile(
    "[" + chr(0x2014) + chr(0x2013) + chr(0x2012) + chr(0x2015) + "]"
)

# Engineering verbs route to pipeline-scaler.
ENGINEERING_TERMS = frozenset(
    {
        "implement",
        "add",
        "fix",
        "refactor",
        "build",
        "create",
        "write",
        "remove",
        "delete",
        "update",
        "modify",
        "change",
    }
)

# Browser / live page terms route to claude-in-chrome.
BROWSER_TERMS = frozenset(
    {
        "chrome",
        "browser",
        "click",
        "screenshot",
        "dom",
        "spa",
        "website",
        "url",
        "http",
        "page",
    }
)


def scan_dashes(prompt: str) -> tuple[int, int, int]:
    """Return (count, first_position, first_codepoint).

    If no banned dash is present, returns (0, -1, 0).
    """
    if not prompt:
        return 0, -1, 0
    matches = list(BANNED_DASH_PATTERN.finditer(prompt))
    if not matches:
        return 0, -1, 0
    first = matches[0]
    return len(matches), first.start(), ord(first.group(0))


def classify_intent(prompt: str) -> tuple[str, list[str]]:
    """Classify the prompt and return (route, matched_terms).

    route is one of: "engineering", "browser", "question".
    Engineering wins over browser when both are present, because the pipeline
    will still dispatch claude-in-chrome inside the engineering track if the
    plan requires it.
    """
    if not prompt:
        return "question", []

    lowered = prompt.lower()
    # Tokenize on word boundaries for precise matching.
    tokens = set(re.findall(r"[a-z]+", lowered))

    eng_hits = sorted(tokens & ENGINEERING_TERMS)
    browser_hits = sorted(tokens & BROWSER_TERMS)

    if eng_hits:
        return "engineering", eng_hits
    if browser_hits:
        return "browser", browser_hits
    return "question", []


def route_for(route: str) -> str:
    if route == "engineering":
        return "pipeline-scaler"
    if route == "browser":
        return "claude-in-chrome"
    return "none"


def ensure_db() -> Optional[sqlite3.Connection]:
    """Open telemetry.sqlite, creating schema if missing. Returns None on any error."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=0.5)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prompt_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                session_id TEXT,
                route TEXT,
                dash_count INTEGER DEFAULT 0,
                prompt_length INTEGER,
                payload_preview TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_prompt_events_session_ts "
            "ON prompt_events(session_id, ts)"
        )
        conn.commit()
        return conn
    except Exception:
        return None


def log_prompt(
    conn: Optional[sqlite3.Connection],
    session_id: str,
    route: str,
    dash_count: int,
    prompt_length: int,
    payload_preview: str,
) -> None:
    """Append a row to prompt_events. Never raises."""
    if conn is None:
        return
    try:
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO prompt_events(
                ts, session_id, route, dash_count, prompt_length, payload_preview
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                session_id or "",
                route or "",
                int(dash_count),
                int(prompt_length),
                payload_preview or "",
            ),
        )
        conn.commit()
    except Exception:
        return


def _truncate(value: Any, limit: int) -> str:
    if value is None:
        return ""
    try:
        text = value if isinstance(value, str) else json.dumps(value, default=str)
    except Exception:
        text = str(value)
    if len(text) > limit:
        return text[:limit]
    return text


def emit(additional_context: str) -> int:
    """Print UserPromptSubmit payload and return 0."""
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context or "",
        }
    }
    try:
        print(json.dumps(payload))
    except Exception:
        print(
            '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit",'
            '"additionalContext":""}}'
        )
    return 0


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return emit("user_prompt_submit: malformed stdin, approving")

    if not isinstance(data, dict):
        return emit("user_prompt_submit: non-object payload, approving")

    prompt = data.get("prompt")
    prompt = prompt if isinstance(prompt, str) else ""
    session_id = str(data.get("session_id") or "")

    # 1. Dash scan (non-blocking).
    dash_count, first_pos, first_cp = scan_dashes(prompt)

    # 2. Intent classification.
    route, hits = classify_intent(prompt)
    suggested = route_for(route)

    # 3. Telemetry (best effort).
    conn = ensure_db()
    try:
        log_prompt(
            conn=conn,
            session_id=session_id,
            route=route,
            dash_count=dash_count,
            prompt_length=len(prompt),
            payload_preview=_truncate(prompt, PAYLOAD_PREVIEW_LIMIT),
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # 4. Build additionalContext summary.
    parts: list[str] = []
    parts.append(f"intent={route}")
    if suggested != "none":
        parts.append(f"suggested_agent={suggested}")
    if hits:
        parts.append("matched=" + ",".join(hits[:6]))
    if dash_count > 0:
        parts.append(
            "dash_warning=count="
            f"{dash_count},first_pos={first_pos},first_codepoint=U+"
            f"{first_cp:04X}"
        )
    parts.append(f"prompt_length={len(prompt)}")

    return emit("user_prompt_submit: " + "; ".join(parts))


if __name__ == "__main__":
    sys.exit(main())
