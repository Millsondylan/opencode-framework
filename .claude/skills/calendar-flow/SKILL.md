---
name: calendar-flow
description: Implement event CRUD, recurrence expansion, and conflict detection for the calendar domain
---

# calendar-flow - Calendar Domain Flow

Implements event CRUD, recurrence expansion, and conflict detection. Third in the calendar domain chain (3/6).

## Usage
```
/calendar-flow
```

## Parameters
- None. This skill consumes calendar-schema and calendar-provider outputs and produces flow artifacts.

## What It Does
1. Implements **CalendarNotifier** — Riverpod StateNotifier for calendar state
2. Defines **CalendarState** — events, selected date, loading, error
3. Registers **calendarProvider**, **eventProvider**, **reminderProvider**
4. Orchestrates **event CRUD** — create, update, delete
5. Orchestrates **recurrence expansion** — expand to date range
6. Implements **conflict detection** — overlapping events
7. Handles **reminder triggers** — schedule, cancel

## Output
- `calendar_notifier.dart` — CalendarNotifier (StateNotifier<CalendarState>)
- `calendar_state.dart` — CalendarState sealed class / union type
- `calendar_provider.dart` — calendarProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (calendar-schema responsibility)
- Write repository or data source code (calendar-provider responsibility)
- Write UI components or screens (calendar-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (event cache via provider)
- **Backend:** Supabase (via calendar-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** calendar (TaskSpec domain)
