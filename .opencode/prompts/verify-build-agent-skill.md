---
skill: auth-schema
category: verification
description: "Verification prompt — dispatches build-agent-1 with skill: auth-schema to verify skill activation"
---

# Verification: Build-Agent Skill Activation

**Purpose:** Verify that build-agent-1 reads `.opencode/skills/auth-schema/SKILL.md` when `skill: auth-schema` is assigned and follows its guidance.

## How to Run

1. **Orchestrator:** Dispatch to build-agent-1 with the prompt below (include `skill: auth-schema` in the prompt).
2. **Expected behavior:** Build-agent reads the skill file before implementing and produces output consistent with auth-schema guidance.

## Verification Prompt (for orchestrator → build-agent-1)

```
<task>Produce a minimal auth schema report per auth-schema skill</task>

<context>
## Skill Assignment
skill: auth-schema

## Requirements
- Read .opencode/skills/auth-schema/SKILL.md before implementing
- Output a minimal markdown report listing: User entity fields, AuthToken model, Role enum values, auth state types
- Do NOT write repository, state management, UI, or tests (per skill constraints)
</context>

<requirements>
- Follow auth-schema skill guidance exactly
- Report must be verifiable: include at least User, AuthToken, Role, and auth state types
</requirements>
```

## Verification Checklist

After build-agent-1 completes, verify:

- [ ] **Skill read:** Build-agent response indicates it read `.opencode/skills/auth-schema/SKILL.md` (or output clearly reflects skill content)
- [ ] **User entity:** Output includes User with id, email, role (or equivalent)
- [ ] **AuthToken:** Output includes AuthToken model
- [ ] **Role enum:** Output includes Role enum
- [ ] **Auth states:** Output includes signed-in, signed-out, loading, error
- [ ] **Constraints respected:** No repository, state management, UI, or test code (per skill "What It Must NOT Do")

## Pass Criteria

**PASS:** All checklist items satisfied.  
**FAIL:** Any item unchecked or output contradicts skill guidance.
