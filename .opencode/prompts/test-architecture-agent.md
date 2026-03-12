---
skill: architecture-agent
category: architecture
description: "Test prompt for architecture-agent skill — produces minimal architecture artifacts"
---

# Test: architecture-agent (Architecture Skill)

Exercises the **architecture-agent** skill. Use with build-agent-1 (or any build-agent) with `skill: architecture-agent` assigned.

## Prompt

```
Implement the app architecture per architecture-agent skill guidance.

skill: architecture-agent

Create a minimal architecture report (or structure) that demonstrates:
1. Clean Architecture layers (domain, data, presentation)
2. Feature-first layout (lib/core/, lib/features/)
3. Entry point (main.dart) and root widget (app.dart)
4. Failures/error handling types

Output: Either a markdown report or architecture-contract.yaml summarizing the structure. Keep footprint minimal.
```

## Expected Verifiable Output

- **Report mode:** Markdown or YAML listing lib/, lib/core/, lib/features/, main.dart, app.dart, failures.dart
- **Contract mode:** `architecture-contract.yaml` with layer and directory definitions

## Verification

1. Build-agent reads `.opencode/skills/architecture-agent/SKILL.md` (evidence: output references Clean Architecture, feature-first, lib/core, lib/features)
2. Output follows skill guidance (no tests, no UI components per skill "What It Must NOT Do")
