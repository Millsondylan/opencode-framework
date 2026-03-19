---
name: code-style-critic
description: dart analyze, naming, import order, lint. Read-only. Outputs code-style-critic-report.json (PASS/FAIL).
---

# code-style-critic - Code Style Validator

Validates code style: dart analyze (or equivalent), naming conventions, import order, lint rules. Read-only. Produces PASS/FAIL report.

## Usage
```
/code-style-critic
```

## Parameters
- **Scope** — Directory or file glob (default: lib/, src/)
- **Lint rules** — Optional custom rule set

## What It Does
1. Runs `dart analyze` (or language equivalent: eslint, ruff, etc.)
2. Checks naming conventions (camelCase, PascalCase, file names)
3. Validates import order and grouping
4. Enforces lint rules from analysis_options / config
5. Produces structured PASS/FAIL report

## Output
- `code-style-critic-report.json` — PASS/FAIL, issues, file:line, rule

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Modify source code (read-only validation)
- Skip any configured lint rules
- Report false positives without verification
