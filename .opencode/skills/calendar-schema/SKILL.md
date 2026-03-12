---
name: calendar-schema
description: Define event, recurrence, reminder, and type IDs 140–149 for the calendar domain
---

# calendar-schema - Calendar Domain Schema

Defines event, recurrence, reminder, and calendar state types for the calendar domain. First in the calendar domain chain (1/6).

## Usage
```
/calendar-schema
```

## Parameters
- None. This skill produces schema artifacts for the calendar domain.

## What It Does
1. Defines **CalendarEvent** entity with Hive persistence (`@HiveType` typeId: 140)
2. Defines **Recurrence** model with Hive persistence (typeId: 141)
3. Defines **Reminder** model with Hive persistence (typeId: 142)
4. Creates **CalendarEventDTO**, **RecurrenceDTO** for API/transport layer
5. Creates **CalendarEventValidator** for input validation
6. Defines recurrence rules (daily, weekly, monthly, custom)

## Output
- `calendar_event.dart` — CalendarEvent model with `@HiveType(typeId: 140)`
- `recurrence.dart` — Recurrence model with `@HiveType(typeId: 141)`
- `reminder.dart` — Reminder model with `@HiveType(typeId: 142)`
- `calendar_event_dto.dart` — CalendarEvent DTO for API/transport
- `recurrence_dto.dart` — Recurrence DTO for API/transport
- `calendar_event_validator.dart` — CalendarEvent input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** calendar (TaskSpec domain)
