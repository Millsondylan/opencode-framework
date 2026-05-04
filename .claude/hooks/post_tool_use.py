#!/usr/bin/env python3
"""
PostToolUse hook for Claude Code.

Runs after any tool invocation completes. Two responsibilities:

1. Quality gate: for Write and Edit tools, execute a syntax check against the
   target file based on its extension. Python, shell, and JSON checks are
   treated as hard checks (result captured). Go is warn-only. YAML is
   opportunistic (only runs if PyYAML is importable; otherwise silent-pass).
   Other extensions are skipped.

2. Telemetry logging: append a row to .claude/hooks/logs/telemetry.sqlite
   describing the tool invocation. The database and its parent directory are
   created on demand. Any failure during logging is swallowed silently.

PostToolUse cannot block: this hook always exits 0 and always prints a valid
JSON object on stdout even when input parsing fails or subprocess checks
crash. The additionalContext field summarizes the syntax-check outcome so the
main model can surface it to the user without reading this file.

Protocol: reads JSON from stdin with fields tool_name, tool_input (file_path,
command), tool_response (success/error), session_id, cwd. Writes one JSON
object to stdout of the form::

    {"hookSpecificOutput":
        {"hookEventName":"PostToolUse",
         "additionalContext":"<summary>"}}

Self-contained: Python 3 stdlib only. No external imports beyond
json, os, sqlite3, subprocess, sys, datetime, pathlib, and typing.

Source file contains zero literal em-dash, en-dash, figure-dash, or
horizontal-bar glyphs. Any reference to banned dashes is constructed via
chr(0x2014) and friends at runtime.

Claude Code hooks reference: https://code.claude.com/docs/en/hooks
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# Paths (module-level so tests and future helpers can import them).
HOOK_DIR = Path(__file__).resolve().parent
LOG_DIR = HOOK_DIR / "logs"
DB_PATH = LOG_DIR / "telemetry.sqlite"

# Maximum characters of command or content to retain in payload_preview.
PAYLOAD_PREVIEW_LIMIT = 1024

# Maximum bytes to capture from a subprocess stdout/stderr stream.
CHECK_OUTPUT_LIMIT = 4096

# Seconds before a syntax check is forcibly aborted.
CHECK_TIMEOUT_SECONDS = 10

# Banned dash class is constructed purely from escape codes so this source
# file itself contains no literal em/en/figure/horizontal-bar glyphs.
# U+2014 EM DASH, U+2013 EN DASH, U+2012 FIGURE DASH, U+2015 HORIZONTAL BAR.
_BANNED_DASH_CHARS = (chr(0x2014), chr(0x2013), chr(0x2012), chr(0x2015))

# Mapping from file extension (lowercase, leading dot) to a handler id. The
# handler id is dispatched inside run_syntax_check to keep the table a pure
# lookup without lambdas stored on disk.
EXT_HANDLERS: dict[str, str] = {
    ".py": "py_compile",
    ".sh": "bash_n",
    ".bash": "bash_n",
    ".json": "json_tool",
    ".go": "gofmt",
    ".yaml": "yaml_safe_load",
    ".yml": "yaml_safe_load",
}

# Extensions whose failure is warn-only (never surfaces as a FAIL status).
WARN_ONLY_EXTS = {".go"}


def ensure_db() -> Optional[sqlite3.Connection]:
    """Create the telemetry directory and table if missing, return a connection.

    Returns None on any error. The caller is responsible for closing the
    connection; since this hook is short-lived, we rely on process exit as a
    fallback if close is skipped after an exception.
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=0.5)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                session_id TEXT,
                tool_name TEXT NOT NULL,
                file_path TEXT,
                exit_status INTEGER,
                duration_ms INTEGER,
                check_result TEXT,
                blocked INTEGER DEFAULT 0,
                reason TEXT,
                payload_preview TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tool_events_session_ts "
            "ON tool_events(session_id, ts)"
        )
        conn.commit()
        return conn
    except Exception:
        return None


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run a command, return (returncode, combined stdout+stderr head)."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
            check=False,
        )
        combined = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, combined[:CHECK_OUTPUT_LIMIT]
    except FileNotFoundError as exc:
        return 127, f"command not found: {exc}"[:CHECK_OUTPUT_LIMIT]
    except subprocess.TimeoutExpired:
        return 124, "syntax check timed out"
    except Exception as exc:
        return 1, f"syntax check raised {type(exc).__name__}: {exc}"[
            :CHECK_OUTPUT_LIMIT
        ]


def _check_py_compile(file_path: str) -> tuple[int, str]:
    return _run([sys.executable, "-m", "py_compile", file_path])


def _check_bash_n(file_path: str) -> tuple[int, str]:
    return _run(["bash", "-n", file_path])


def _check_json_tool(file_path: str) -> tuple[int, str]:
    # json.tool writes reformatted JSON to stdout; suppress it by discarding.
    rc, out = _run([sys.executable, "-m", "json.tool", file_path])
    if rc == 0:
        return rc, ""
    return rc, out


def _check_gofmt(file_path: str) -> tuple[int, str]:
    # gofmt -l prints filenames whose formatting differs; empty stdout = ok.
    rc, out = _run(["gofmt", "-l", file_path])
    # Warn-only: even non-zero output is not a blocking failure.
    return rc, out


def _check_yaml(file_path: str) -> tuple[int, str]:
    script = (
        "import sys\n"
        "try:\n"
        "    import yaml\n"
        "except ImportError:\n"
        "    sys.exit(0)\n"
        "try:\n"
        "    with open(sys.argv[1], 'r', encoding='utf-8') as fh:\n"
        "        yaml.safe_load(fh)\n"
        "except Exception as exc:\n"
        "    sys.stderr.write(str(exc))\n"
        "    sys.exit(1)\n"
    )
    return _run([sys.executable, "-c", script, file_path])


def run_syntax_check(file_path: str) -> tuple[str, int, str]:
    """Dispatch a syntax check based on file extension.

    Returns a tuple (check_name, exit_status, output_head).

    - check_name is "none" when no handler matches.
    - exit_status is 0 on pass, non-zero on fail. For warn-only extensions
      (currently .go and .yaml when PyYAML is absent), we normalize the
      return to 0 while preserving the handler name and any output.
    """
    if not file_path:
        return "none", 0, ""

    path = Path(file_path)
    ext = path.suffix.lower()
    handler = EXT_HANDLERS.get(ext)
    if handler is None:
        return "none", 0, ""

    # If the file does not exist (for example Edit on a removed file) do not
    # attempt to shell out. Report it as a pass with a note so callers can
    # correlate against tool_response.
    if not path.is_file():
        return handler, 0, f"file missing: {file_path}"

    if handler == "py_compile":
        rc, out = _check_py_compile(str(path))
    elif handler == "bash_n":
        rc, out = _check_bash_n(str(path))
    elif handler == "json_tool":
        rc, out = _check_json_tool(str(path))
    elif handler == "gofmt":
        rc, out = _check_gofmt(str(path))
    elif handler == "yaml_safe_load":
        rc, out = _check_yaml(str(path))
    else:
        return "none", 0, ""

    # Warn-only: never propagate failure.
    if ext in WARN_ONLY_EXTS:
        return handler, 0, out

    return handler, rc, out


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


def _payload_preview(tool_input: Any) -> str:
    """Compact snippet describing the tool payload. Never raises."""
    try:
        if isinstance(tool_input, dict):
            # Prefer the highest-signal fields first.
            for key in ("command", "content", "new_string", "file_path"):
                val = tool_input.get(key)
                if isinstance(val, str) and val:
                    return _truncate(val, PAYLOAD_PREVIEW_LIMIT)
            return _truncate(tool_input, PAYLOAD_PREVIEW_LIMIT)
        if tool_input is None:
            return ""
        return _truncate(tool_input, PAYLOAD_PREVIEW_LIMIT)
    except Exception:
        return ""


def _response_exit_status(tool_response: Any) -> Optional[int]:
    """Best-effort extraction of an exit code from tool_response."""
    if not isinstance(tool_response, dict):
        return None
    for key in ("exit_status", "exitCode", "exit_code", "status"):
        val = tool_response.get(key)
        if isinstance(val, int):
            return val
    if tool_response.get("error"):
        return 1
    success = tool_response.get("success")
    if isinstance(success, bool):
        return 0 if success else 1
    return None


def log_event(
    conn: Optional[sqlite3.Connection],
    session_id: str,
    tool_name: str,
    file_path: str,
    exit_status: Optional[int],
    duration_ms: Optional[int],
    check_result: str,
    blocked: int,
    reason: str,
    payload_preview: str,
) -> None:
    """Append a row to tool_events. Never raises."""
    if conn is None:
        return
    try:
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO tool_events(
                ts, session_id, tool_name, file_path, exit_status,
                duration_ms, check_result, blocked, reason, payload_preview
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                session_id or "",
                tool_name or "",
                file_path or "",
                exit_status,
                duration_ms,
                check_result or "",
                int(blocked),
                reason or "",
                payload_preview or "",
            ),
        )
        conn.commit()
    except Exception:
        return


def _emit(additional_context: str) -> int:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional_context or "",
        }
    }
    try:
        print(json.dumps(payload))
    except Exception:
        # Fallback minimal emit if json.dumps somehow fails.
        print('{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":""}}')
    return 0


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Silent approve with explanatory context.
        return _emit("post_tool_use: malformed stdin, approving")

    if not isinstance(data, dict):
        return _emit("post_tool_use: non-object payload, approving")

    tool_name = str(data.get("tool_name") or "")
    tool_input = data.get("tool_input") or {}
    tool_response = data.get("tool_response") or {}
    session_id = str(data.get("session_id") or "")

    file_path = ""
    if isinstance(tool_input, dict):
        fp = tool_input.get("file_path")
        if isinstance(fp, str):
            file_path = fp

    # Quality gate applies only to Write and Edit style tools.
    name_lower = tool_name.lower()
    check_name = "none"
    check_rc: Optional[int] = None
    check_output = ""
    if name_lower in {"write", "edit", "multiedit"} and file_path:
        check_name, check_rc, check_output = run_syntax_check(file_path)

    # Build the check_result summary used for telemetry and additionalContext.
    if check_name == "none":
        check_result = "skipped"
        summary = f"quality-gate: skipped for {tool_name or 'tool'}"
    elif check_rc == 0:
        check_result = f"{check_name}:pass"
        summary = f"quality-gate: {check_name} PASS on {file_path}"
    else:
        head = (check_output or "").strip().splitlines()
        head_line = head[0][:240] if head else ""
        check_result = f"{check_name}:fail(rc={check_rc})"
        summary = (
            f"quality-gate: {check_name} FAIL on {file_path} "
            f"(rc={check_rc}): {head_line}"
        )

    exit_status = _response_exit_status(tool_response)
    payload_preview = _payload_preview(tool_input)

    conn = ensure_db()
    try:
        log_event(
            conn=conn,
            session_id=session_id,
            tool_name=tool_name,
            file_path=file_path,
            exit_status=exit_status,
            duration_ms=None,
            check_result=check_result,
            blocked=0,
            reason=summary if check_result.endswith("fail") else "",
            payload_preview=payload_preview,
        )
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # Memory update hook: best effort no-op. The memory consolidator daemon
    # (Run 3/8) is responsible for appending to lessons.md when it exists.
    _ = Path(HOOK_DIR.parent, ".memory", "lessons.md")

    return _emit(summary)


if __name__ == "__main__":
    sys.exit(main())
