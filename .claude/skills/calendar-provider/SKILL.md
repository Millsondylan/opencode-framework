---
name: calendar-provider
description: Implement device calendar and reminder scheduling for the calendar domain
---

# calendar-provider - Calendar Domain Provider

Implements device calendar and reminder scheduling. Second in the calendar domain chain (2/6).

## Usage
```
/calendar-provider
```

## Parameters
- None. This skill consumes calendar-schema outputs and produces provider artifacts.

## What It Does
1. Implements **CalendarRepository** — domain-facing repository interface
2. Implements **DeviceCalendarDataSource** — device calendar plugin (iOS/Android)
3. Implements **CalendarRemoteDataSource** — Supabase sync
4. Implements **ReminderScheduler** — local notifications, reminder triggers
5. Handles **event CRUD** — create, read, update, delete
6. Handles **recurrence expansion** — expand recurring events to instances

## Output
- `calendar_repository.dart` — CalendarRepository implementation
- `device_calendar_data_source.dart` — Device calendar plugin wrapper
- `calendar_remote_data_source.dart` — Supabase client
- `reminder_scheduler.dart` — Reminder scheduling

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (calendar-schema responsibility)
- Write flow/state orchestration (calendar-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase
- **Plugins:** device_calendar, flutter_local_notifications
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** calendar (TaskSpec domain)
