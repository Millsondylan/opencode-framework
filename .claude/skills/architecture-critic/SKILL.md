---
name: architecture-critic
description: Layer boundaries — no UI importing data, no business logic in widgets
---

# architecture-critic - Architecture Layer Validator

Validates architecture layer boundaries: no UI importing data layer directly, no business logic in widgets. Enforces clean architecture / layered design.

## Usage
```
/architecture-critic
```

## Parameters
- **Layer config** — Optional layer definitions (ui, domain, data, etc.)
- **Scope** — Directory to analyze (default: full app)

## What It Does
1. Maps imports and dependencies between layers
2. Flags UI importing data/repository directly
3. Flags business logic in widgets or UI components
4. Validates dependency direction (inner layers not depending on outer)
5. Produces structured report with violations

## Output
- `architecture-report.json` — Violations, file:line, layer, recommendation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Modify source code (read-only validation)
- Ignore transitive or re-exported dependencies
- Assume single architecture pattern (adapt to project structure)
