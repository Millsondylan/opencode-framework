---
name: analytics-schema
description: Define event models, funnel, and type IDs 70–79 for the analytics domain
---

# analytics-schema - Analytics Domain Schema

Defines event models, funnel types, and analytics state for the analytics domain. First in the analytics domain chain (1/6).

## Usage
```
/analytics-schema
```

## Parameters
- None. This skill produces schema artifacts for the analytics domain.

## What It Does
1. Defines **AnalyticsEvent** entity with Hive persistence (`@HiveType` typeId: 70)
2. Defines **FunnelStep** model with Hive persistence (typeId: 71)
3. Defines **Session** model with Hive persistence (typeId: 72)
4. Creates **AnalyticsEventDTO** and **FunnelStepDTO** for API/transport layer
5. Creates **AnalyticsEventValidator** for input validation
6. Defines event types (screen_view, user_action, conversion, custom)

## Output
- `analytics_event.dart` — AnalyticsEvent model with `@HiveType(typeId: 70)`
- `funnel_step.dart` — FunnelStep model with `@HiveType(typeId: 71)`
- `session.dart` — Session model with `@HiveType(typeId: 72)`
- `analytics_event_dto.dart` — AnalyticsEvent DTO for API/transport
- `funnel_step_dto.dart` — FunnelStep DTO for API/transport
- `analytics_event_validator.dart` — AnalyticsEvent input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** analytics (TaskSpec domain)
