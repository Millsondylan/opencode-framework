---
name: calendar-guard
description: Implement permissions and overlap validation for the calendar domain
---

# calendar-guard - Calendar Domain Guard

Implements permissions and overlap validation. Fifth in the calendar domain chain (5/6).

## Usage
```
/calendar-guard
```

## Parameters
- None. This skill consumes calendar-schema and calendar-provider outputs and produces guard artifacts.

## What It Does
1. Implements **CalendarPermissionGuard** — check, request calendar/reminder access
2. Implements **OverlapValidationGuard** — validate no conflicting events (optional policy)
3. Integrates with Riverpod calendar state for guard decisions
4. Handles **permission flow** — rationale, settings redirect
5. Handles **platform-specific** — iOS vs Android permission models

## Output
- `calendar_permission_guard.dart` — CalendarPermissionGuard
- `overlap_validation_guard.dart` — OverlapValidationGuard

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (calendar-schema responsibility)
- Write provider/repository code (calendar-provider responsibility)
- Write flow/state orchestration (calendar-flow responsibility)
- Write UI components or screens
- Write tests (calendar-test responsibility)

## Tech Stack
- **State:** Riverpod (reads calendar state for guard decisions)
- **Plugins:** permission_handler
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** calendar (TaskSpec domain)
