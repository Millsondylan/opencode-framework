#!/usr/bin/env python3
"""
SubagentStop hook: inject skill-activation reminder for the orchestrator after a subagent finishes.

Claude Code docs: SubagentStop receives agent_type; hookSpecificOutput.additionalContext is added
to the conversation. See https://code.claude.com/docs/en/hooks#subagentstop
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
    skill_hint = ""
    if agent.startswith("build-agent") or agent in (
        "test-writer",
        "docs-researcher",
        "test-agent",
    ):
        skill_hint = (
            " If the plan batch named a **Skill:**, the next implementation step MUST load "
            "`.claude/skills/<name>/SKILL.md` (or use Skill(name)) before editing code."
        )

    ctx = (
        f"[subagent-stop] `{agent}` completed. PostToolUse Task validators already ran on tool output.{skill_hint} "
        "Skill index: `.claude/skills/INDEX.md`. Hooks reference: https://code.claude.com/docs/en/hooks"
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
