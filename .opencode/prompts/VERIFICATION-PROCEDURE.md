# Build-Agent Skill Activation Verification

This document describes how to verify that build-agents correctly read and follow skill guidance when `skill: {name}` is assigned.

## Overview

When the orchestrator dispatches to a build-agent with `skill: auth-schema` (or any skill), the build-agent must:

1. Read `.opencode/skills/{name}/SKILL.md` before implementing
2. Follow the skill's guidance during implementation
3. Respect the skill's "What It Must NOT Do" constraints

## Verification Procedure

### Method 1: Direct Verification (Recommended)

Use the verification prompt to dispatch build-agent-1 with `skill: auth-schema`:

1. **Open** `.opencode/prompts/verify-build-agent-skill.md`
2. **Copy** the "Verification Prompt" section
3. **Dispatch** to build-agent-1 via the task tool with that prompt as the `prompt` parameter
4. **Evaluate** the build-agent output using the checklist in the same file

### Method 2: Orchestrator Flow

If using the full pipeline:

1. **Task:** "Add auth domain schema per auth-schema skill"
2. **Plan-agent** should assign `skill: auth-schema` to the relevant batch
3. **Orchestrator** passes the prompt to build-agent-1 with `skill: auth-schema` in context
4. **Verify** build-agent output references auth-schema guidance or produces auth-schema artifacts

### Method 3: Minimal Integration Test (Script)

If you have a script that invokes the agent:

```bash
# Example: verify skill is passed when dispatching
# (Replace with actual invocation mechanism)
echo "skill: auth-schema" > /tmp/skill-prompt.txt
# Dispatch build-agent-1 with prompt containing skill assignment
# Verify output contains auth-schema artifacts (User, AuthToken, Role, etc.)
```

## Evidence of Skill Activation

The build-agent **has activated** the skill if the output contains:

- References to skill-specific concepts (e.g., User, AuthToken, Role, Hive typeIds for auth-schema)
- Structure matching the skill's "Output" section
- No violations of the skill's "What It Must NOT Do" section

## Pass/Fail Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Skill file read | Output reflects skill content | Generic output, no skill-specific concepts |
| Guidance followed | Output matches skill Output section | Output contradicts skill |
| Constraints respected | No forbidden artifacts | Repository, UI, tests, etc. written when forbidden |

## Files

- **Verification prompt:** `.opencode/prompts/verify-build-agent-skill.md`
- **Skill under test:** `.opencode/skills/auth-schema/SKILL.md`
- **Build-agent definition:** `.opencode/agents/build-agent-1.md` (Skill Activation section)
