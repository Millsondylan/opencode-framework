---
name: calendar-ui
description: Implement CalendarView, EventFormScreen, and agenda for the calendar domain
---

# calendar-ui - Calendar Domain UI

Implements CalendarView, EventFormScreen, and agenda. Fourth in the calendar domain chain (4/6).

## Usage
```
/calendar-ui
```

## Parameters
- None. This skill consumes calendar-flow outputs and produces UI artifacts.

## What It Does
1. Implements **CalendarView** — month/week/day view, date picker
2. Implements **EventFormScreen** — create/edit event, recurrence picker
3. Implements **AgendaView** — event list for selected date
4. Implements **EventTile** — event display, time, title, reminder
5. Handles **conflict UI** — warn on overlap, suggest alternatives
6. Uses **Material 3** — components, theming, typography

## Output
- `calendar_view.dart` — CalendarView widget
- `event_form_screen.dart` — EventFormScreen widget
- `agenda_view.dart` — AgendaView widget
- `event_tile.dart` — EventTile widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (calendar-schema responsibility)
- Write repository or data source code (calendar-provider responsibility)
- Write flow/state orchestration (calendar-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter), table_calendar or similar
- **State:** Riverpod (read calendarProvider, call CalendarNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** calendar (TaskSpec domain)
