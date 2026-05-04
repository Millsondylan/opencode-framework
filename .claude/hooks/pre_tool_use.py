#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code.

Enforces four policies before any tool invocation is allowed:

1. Banned dash characters (U+2014 em, U+2013 en, U+2012 figure, U+2015 horizontal bar).
2. Hardcoded secret patterns (API keys, private keys, tokens, passwords).
3. Banned email libraries (smtplib, nodemailer, sendgrid, etc.) per rule 13 (spacemail-only).
4. Destructive shell commands (rm -rf, DROP DATABASE, git push --force, fork bomb)
   unless the command contains literal "CONFIRM_DESTRUCTIVE".

Protocol: reads JSON from stdin with fields tool_name, tool_input, session_id, cwd.
Writes JSON to stdout with decision ("approve" or "block") and reason.
Exit code 0 = approve, exit code 2 = block.

Telemetry: best-effort INSERT into .claude/hooks/logs/telemetry.sqlite if present.
Failures in telemetry are silent and never block the main decision.

Self-contained: Python 3 stdlib only (json, re, sys, os, sqlite3, time).
No literal em-dash, en-dash, figure-dash, or horizontal-bar characters in source;
all banned dash glyphs are expressed via \\u escape sequences.

Claude Code hooks reference: https://code.claude.com/docs/en/hooks
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
from typing import Iterable


# Banned dash class expressed only via unicode escapes so this source file
# itself contains zero literal em/en/figure/horizontal-bar glyphs.
# U+2014 EM DASH, U+2013 EN DASH, U+2012 FIGURE DASH, U+2015 HORIZONTAL BAR.
BANNED_DASH_PATTERN = re.compile(
    "[" + chr(0x2014) + chr(0x2013) + chr(0x2012) + chr(0x2015) + "]"
)

# Secret patterns (from project CLAUDE.md security rules).
SECRET_PATTERNS: list[tuple[str, re.Pattern[str], int]] = [
    ("anthropic_api_key", re.compile(r"sk-ant-[a-zA-Z0-9]{10,}"), 0),
    ("anthropic_project_key", re.compile(r"sk-proj-[a-zA-Z0-9]{10,}"), 0),
    ("generic_sk_key", re.compile(r"sk-[a-zA-Z0-9]{20,}"), 0),
    ("aws_access_key_id", re.compile(r"AKIA[A-Z0-9]{16}"), 0),
    (
        "aws_secret_access_key",
        re.compile(r"AWS_SECRET_ACCESS_KEY\s*=\s*[\"'][^\"']{20,}"),
        0,
    ),
    (
        "pem_private_key",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        0,
    ),
    (
        "api_key_assignment",
        re.compile(r"(?:API_KEY|API_SECRET)\s*=\s*[\"'][^\"']{8,}"),
        0,
    ),
    (
        "hardcoded_password",
        re.compile(r"(?:password|passwd)\s*=\s*[\"'][^\"']{4,}", re.IGNORECASE),
        0,
    ),
    ("github_pat", re.compile(r"ghp_[a-zA-Z0-9]{36,}"), 0),
    ("github_server_token", re.compile(r"ghs_[a-zA-Z0-9]{36,}"), 0),
    ("gitlab_pat", re.compile(r"glpat-[a-zA-Z0-9\-]{20,}"), 0),
    ("bearer_token", re.compile(r"Bearer [a-zA-Z0-9.\-_]{20,}"), 0),
]

# Banned email library patterns (rule 13: spacemail-only).
EMAIL_LIB_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "python_email_import",
        re.compile(
            r"^\s*(?:from\s+(?:smtplib|aiosmtplib|sendgrid|mailgun|postmark|resend)"
            r"|import\s+(?:smtplib|aiosmtplib|sendgrid|mailgun|postmark|resend))",
            re.MULTILINE,
        ),
    ),
    (
        "js_email_import",
        re.compile(
            r"(?:require|import).*(?:nodemailer|@sendgrid/mail|mailgun\.js|postmark|@aws-sdk/client-ses|resend)"
        ),
    ),
    (
        "banned_email_url",
        re.compile(
            r"(?:smtp\.|api\.sendgrid\.com|api\.mailgun\.net|api\.postmarkapp\.com)"
        ),
    ),
]

# Destructive shell patterns.
DESTRUCTIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("rm_recursive_force", re.compile(r"rm\s+(-[a-zA-Z]*[rf]|--recursive|--force).*/")),
    ("sql_drop", re.compile(r"DROP\s+(DATABASE|TABLE|SCHEMA)", re.IGNORECASE)),
    ("git_force_push", re.compile(r"git\s+push.*--force")),
    ("git_reset_hard", re.compile(r"git\s+reset\s+--hard")),
    ("fork_bomb", re.compile(r":\(\)\{\s*:\|:&\s*\};:")),
]

CONFIRM_TOKEN = "CONFIRM_DESTRUCTIVE"

TELEMETRY_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "telemetry.sqlite"
)


def extract_strings(tool_name: str, tool_input: object) -> list[tuple[str, str]]:
    """Return (key, value) tuples of inspectable string fields from tool_input.

    Focuses on fields likely to contain code or shell the user is about to run or write.
    """
    out: list[tuple[str, str]] = []
    if not isinstance(tool_input, dict):
        return out

    name = (tool_name or "").lower()

    priority_keys: tuple[str, ...]
    if name in {"write", "edit", "multiedit"}:
        priority_keys = ("content", "new_string", "old_string", "file_path")
    elif name == "bash":
        priority_keys = ("command",)
    else:
        priority_keys = ()

    seen: set[str] = set()

    for key in priority_keys:
        if key in tool_input:
            val = tool_input.get(key)
            if isinstance(val, str):
                out.append((key, val))
                seen.add(key)

    # For MultiEdit, iterate the edits array for per-edit old/new strings.
    if name == "multiedit":
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            for i, edit in enumerate(edits):
                if isinstance(edit, dict):
                    for sub in ("old_string", "new_string"):
                        v = edit.get(sub)
                        if isinstance(v, str):
                            out.append((f"edits[{i}].{sub}", v))

    # Catch-all: any other top-level string values we have not already captured.
    for key, val in tool_input.items():
        if key in seen:
            continue
        if isinstance(val, str):
            out.append((key, val))

    return out


def check_dash(s: str) -> tuple[bool, int]:
    """Return (hit, position) if a banned dash glyph is found."""
    m = BANNED_DASH_PATTERN.search(s)
    if m:
        return True, m.start()
    return False, -1


def check_secrets(s: str) -> tuple[bool, str]:
    """Return (hit, pattern_name) if any secret pattern matches."""
    for name, pattern, _flags in SECRET_PATTERNS:
        if pattern.search(s):
            return True, name
    return False, ""


def check_email_libs(file_path: str, content: str) -> tuple[bool, str]:
    """Return (hit, match_string) if a banned email lib is used.

    Only inspects Python (.py) and JS/TS (.js, .jsx, .ts, .tsx, .mjs, .cjs) contexts,
    or any content containing banned email URLs.
    """
    if not content:
        return False, ""

    fp_lower = (file_path or "").lower()
    is_py = fp_lower.endswith(".py")
    is_js = fp_lower.endswith(
        (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")
    )

    for name, pattern in EMAIL_LIB_PATTERNS:
        if name == "python_email_import" and not is_py:
            continue
        if name == "js_email_import" and not is_js:
            continue
        m = pattern.search(content)
        if m:
            return True, f"{name}:{m.group(0)[:80]}"
    return False, ""


def check_destructive(command: str) -> tuple[bool, str]:
    """Return (hit, pattern_name) if a destructive shell pattern matches."""
    if not command:
        return False, ""
    for name, pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, name
    return False, ""


def log_telemetry(tool_name: str, decision: str, reason: str) -> None:
    """Best-effort append to telemetry.sqlite. Never raises."""
    try:
        if not os.path.exists(TELEMETRY_DB):
            return
        conn = sqlite3.connect(TELEMETRY_DB, timeout=0.5)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_events (
                    ts REAL NOT NULL,
                    tool_name TEXT,
                    decision TEXT,
                    reason TEXT
                )
                """
            )
            conn.execute(
                "INSERT INTO tool_events(ts, tool_name, decision, reason) VALUES (?, ?, ?, ?)",
                (time.time(), tool_name or "", decision or "", reason or ""),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # Silent: telemetry must never block or crash the hook.
        return


def emit(decision: str, reason: str, tool_name: str) -> int:
    """Print the decision JSON to stdout and return the exit code."""
    payload = {
        "decision": decision,
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "toolName": tool_name or "",
        },
    }
    print(json.dumps(payload))
    log_telemetry(tool_name, decision, reason)
    return 0 if decision == "approve" else 2


def iter_strings(pairs: Iterable[tuple[str, str]]) -> Iterable[tuple[str, str]]:
    for key, val in pairs:
        if isinstance(val, str) and val:
            yield key, val


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Malformed input: fail open (approve) so we do not deadlock the session.
        return emit("approve", "pre_tool_use: malformed stdin, approving", "")

    if not isinstance(data, dict):
        return emit("approve", "pre_tool_use: non-object payload, approving", "")

    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}

    pairs = extract_strings(tool_name, tool_input)

    # 1. Dash check across every inspectable string.
    for key, val in iter_strings(pairs):
        hit, pos = check_dash(val)
        if hit:
            ch = val[pos] if 0 <= pos < len(val) else "?"
            codepoint = ord(ch) if ch != "?" else 0
            reason = (
                "Banned dash character (U+"
                f"{codepoint:04X}) detected in field '{key}' at position {pos}. "
                "Use ASCII hyphen, colon, or period instead."
            )
            return emit("block", reason, tool_name)

    # 2. Secret check.
    for key, val in iter_strings(pairs):
        hit, pname = check_secrets(val)
        if hit:
            reason = (
                f"Secret pattern '{pname}' detected in field '{key}'. "
                "Remove credential, use environment variables or a secrets manager."
            )
            return emit("block", reason, tool_name)

    # 3. Banned email library check (Write/Edit/MultiEdit only).
    name_lower = (tool_name or "").lower()
    if name_lower in {"write", "edit", "multiedit"} and isinstance(tool_input, dict):
        file_path = tool_input.get("file_path") or ""
        # Aggregate all content-ish strings for email lib scan.
        contentish = []
        for key in ("content", "new_string"):
            v = tool_input.get(key)
            if isinstance(v, str):
                contentish.append(v)
        if name_lower == "multiedit":
            edits = tool_input.get("edits")
            if isinstance(edits, list):
                for e in edits:
                    if isinstance(e, dict):
                        nv = e.get("new_string")
                        if isinstance(nv, str):
                            contentish.append(nv)
        joined = "\n".join(contentish)
        hit, match = check_email_libs(
            file_path if isinstance(file_path, str) else "", joined
        )
        if hit:
            reason = (
                f"Banned email library usage detected ({match}). "
                "Rule 13-spacemail-only: all outbound email must route through "
                "the Spacemail provider. Remove this import and use the approved client."
            )
            return emit("block", reason, tool_name)

    # 4. Destructive shell check (Bash only).
    if name_lower == "bash" and isinstance(tool_input, dict):
        command = tool_input.get("command") or ""
        if isinstance(command, str):
            hit, pname = check_destructive(command)
            if hit and CONFIRM_TOKEN not in command:
                reason = (
                    f"Destructive shell pattern '{pname}' detected. "
                    f"Include the literal token {CONFIRM_TOKEN} in the command to acknowledge, "
                    "or use a safer alternative. Refer to .claude/rules/05-operational-policies.md."
                )
                return emit("block", reason, tool_name)

    return emit("approve", "pre_tool_use checks passed", tool_name)


if __name__ == "__main__":
    sys.exit(main())
