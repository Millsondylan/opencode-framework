---
name: calendar-test
description: Write recurrence and conflict tests for the calendar domain
---

# calendar-test - Calendar Domain Test

Writes recurrence and conflict tests. Sixth in the calendar domain chain (6/6).

## Usage
```
/calendar-test
```

## Parameters
- None. This skill consumes all prior calendar domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for calendar logic (validators, guards, recurrence)
2. Writes **recurrence tests** — expansion, RRULE parsing
3. Writes **conflict tests** — overlap detection, resolution
4. Provides **mock calendar repository** for isolated testing
5. Achieves **>80% coverage** for calendar domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `calendar_repository_test.dart` — Unit tests for CalendarRepository
- `calendar_notifier_test.dart` — Unit tests for CalendarNotifier
- `recurrence_test.dart` — Recurrence expansion tests
- `conflict_test.dart` — Conflict detection tests
- `mock_calendar_repository.dart` — Mock calendar repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production calendar logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** calendar (TaskSpec domain)
