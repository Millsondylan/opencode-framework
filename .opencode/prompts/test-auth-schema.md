---
skill: auth-schema
category: domain-chain
description: "Test prompt for auth-schema skill — produces minimal auth schema artifacts"
---

# Test: auth-schema (Domain Chain Skill)

Exercises the **auth-schema** skill. Use with build-agent-1 (or any build-agent) with `skill: auth-schema` assigned.

## Prompt

```
Implement the auth domain schema per auth-schema skill guidance.

skill: auth-schema

Create a minimal auth schema report (or stub files) that demonstrates:
1. User entity structure (id, email, role)
2. AuthToken model structure
3. Role enum values
4. Auth state types (signed-in, signed-out, loading, error)

Output: Either a markdown report summarizing the schema, or minimal Dart stubs in lib/domain/auth/ if the project has a Flutter structure. Keep footprint minimal.
```

## Expected Verifiable Output

- **Report mode:** Markdown document listing User, AuthToken, Role, auth state types
- **Code mode:** At least one of: `user_entity.dart`, `auth_token.dart`, `role.dart`, or equivalent stubs

## Verification

1. Build-agent reads `.opencode/skills/auth-schema/SKILL.md` (evidence: output references User, AuthToken, Role, Hive typeIds, or auth state types)
2. Output follows skill guidance (no repository, state management, UI, or tests per skill "What It Must NOT Do")
