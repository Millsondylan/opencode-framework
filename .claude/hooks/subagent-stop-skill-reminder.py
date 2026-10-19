#!/usr/bin/env python3
"""
SubagentStop hook: skill reminder after implementation-related subagents finish.

Only runs for matcher build-agent.*|test-writer|docs-researcher|test-agent (see settings.json).

Claude Code docs: https://code.claude.com/docs/en/hooks#subagentstop
"""
import json
import sys


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        sys.exit(0)

    agent = (data.get("agent_type") or "unknown").strip()
    ctx = (
        f"[subagent-stop] `{agent}` completed. PostToolUse Task validators already ran on tool output. "
        "If the plan batch named a **Skill:**, the next step MUST load `.claude/skills/<name>/SKILL.md` "
        "(or use Skill(name)) before editing code. Skill index: `.claude/skills/INDEX.md`. "
        "Hooks: https://code.claude.com/docs/en/hooks"
    )

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStop",
                    "additionalContext": ctx,
                }
            }
        )
    )


if __name__ == "__main__":
    main()
