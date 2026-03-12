---
name: completeness-critic
description: Every screen has loading/empty/error/populated; every async has error handling
---

# completeness-critic - Completeness Validator

Validates completeness: every screen has loading/empty/error/populated states; every async operation has error handling.

## Usage
```
/completeness-critic
```

## Parameters
- **Screens** — List or glob of screens to check
- **Async patterns** — Optional (Future, Stream, async/await)

## What It Does
1. Identifies all screens and their state handling
2. Checks for loading state (spinner, skeleton, etc.)
3. Checks for empty state (no data UI)
4. Checks for error state (error message, retry)
5. Checks for populated state (success content)
6. Validates async operations have try/catch or error handling
7. Produces structured report

## Output
- `completeness-report.json` — Missing states per screen, async without error handling, recommendations

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Modify source code (read-only validation)
- Assume single state pattern (adapt to Bloc, Riverpod, etc.)
- Ignore partial implementations (e.g., loading but no error)
