---
name: analytics-flow
description: Implement event dispatch, session tracking, and screen logging for the analytics domain
---

# analytics-flow - Analytics Domain Flow

Implements event dispatch, session tracking, and screen logging. Third in the analytics domain chain (3/6).

## Usage
```
/analytics-flow
```

## Parameters
- None. This skill consumes analytics-schema and analytics-provider outputs and produces flow artifacts.

## What It Does
1. Implements **AnalyticsNotifier** — Riverpod StateNotifier for analytics state
2. Defines **AnalyticsState** — enabled, disabled, consent-pending
3. Registers **analyticsProvider** — Riverpod provider exposing AnalyticsNotifier
4. Orchestrates **event dispatch** — log event → validate → batch → send
5. Tracks **session** — start, end, duration, screen sequence
6. Implements **screen logging** — automatic screen_view on navigation
7. Handles **flush** — manual or scheduled batch send

## Output
- `analytics_notifier.dart` — AnalyticsNotifier (StateNotifier<AnalyticsState>)
- `analytics_state.dart` — AnalyticsState sealed class / union type
- `analytics_provider.dart` — analyticsProvider (Riverpod Provider)
- Session and screen logging integration

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (analytics-schema responsibility)
- Write repository or data source code (analytics-provider responsibility)
- Write UI components or screens (analytics-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (offline queue via provider)
- **Backend:** Firebase/Mixpanel (via analytics-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** analytics (TaskSpec domain)
