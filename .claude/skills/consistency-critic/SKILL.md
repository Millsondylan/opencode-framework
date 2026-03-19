---
name: consistency-critic
description: Naming, file org, import style consistent across codebase
---

# consistency-critic - Consistency Validator

Validates consistency: naming conventions, file organization, import style consistent across the codebase.

## Usage
```
/consistency-critic
```

## Parameters
- **Scope** — Directory to analyze (default: full app)
- **Conventions** — Optional project-specific rules

## What It Does
1. Audits naming (files, classes, functions, variables)
2. Checks file organization (folder structure, co-location)
3. Validates import style (order, aliases, relative vs absolute)
4. Flags inconsistencies (e.g., mixed naming, scattered similar files)
5. Produces structured report with recommendations

## Output
- `consistency-report.json` — Inconsistencies, examples, recommended pattern

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Modify source code (read-only validation)
- Enforce arbitrary rules not aligned with project
- Report minor stylistic preferences as failures
