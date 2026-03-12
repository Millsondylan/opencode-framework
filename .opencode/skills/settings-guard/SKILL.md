---
name: settings-guard
description: Implement preference validation and schema migration for the settings domain
---

# settings-guard - Settings Domain Guard

Implements preference validation and schema migration. Fifth in the settings domain chain (5/6).

## Usage
```
/settings-guard
```

## Parameters
- None. This skill consumes settings-schema and settings-provider outputs and produces guard artifacts.

## What It Does
1. Implements **PreferenceValidationGuard** — validates preference values before persist
2. Implements **SchemaMigrationGuard** — migrates old preference formats to new
3. Integrates with Riverpod settings state for guard decisions
4. Handles **default fallback** — invalid values → defaults
5. Handles **version compatibility** — app upgrade compatibility

## Output
- `preference_validation_guard.dart` — PreferenceValidationGuard
- `schema_migration_guard.dart` — SchemaMigrationGuard

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (settings-schema responsibility)
- Write provider/repository code (settings-provider responsibility)
- Write flow/state orchestration (settings-flow responsibility)
- Write UI components or screens
- Write tests (settings-test responsibility)

## Tech Stack
- **State:** Riverpod (reads settings state for guard decisions)
- **Storage:** Hive (preference persistence)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** settings (TaskSpec domain)
