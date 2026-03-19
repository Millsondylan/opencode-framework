---
name: maps-guard
description: Implement location permissions and background location for the maps domain
---

# maps-guard - Maps Domain Guard

Implements location permissions and background location. Fifth in the maps domain chain (5/6).

## Usage
```
/maps-guard
```

## Parameters
- None. This skill consumes maps-schema and maps-provider outputs and produces guard artifacts.

## What It Does
1. Implements **LocationPermissionGuard** — check, request, handle denied
2. Implements **BackgroundLocationGuard** — background mode, battery optimization
3. Integrates with Riverpod maps state for guard decisions
4. Handles **permission flow** — rationale, settings redirect
5. Handles **platform-specific** — iOS vs Android permission models

## Output
- `location_permission_guard.dart` — LocationPermissionGuard
- `background_location_guard.dart` — BackgroundLocationGuard

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (maps-schema responsibility)
- Write provider/repository code (maps-provider responsibility)
- Write flow/state orchestration (maps-flow responsibility)
- Write UI components or screens
- Write tests (maps-test responsibility)

## Tech Stack
- **State:** Riverpod (reads maps state for guard decisions)
- **Plugins:** permission_handler
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** maps (TaskSpec domain)
