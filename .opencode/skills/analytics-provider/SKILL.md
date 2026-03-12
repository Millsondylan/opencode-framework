---
name: analytics-provider
description: Implement Firebase/Mixpanel integration, batching, and event persistence for the analytics domain
---

# analytics-provider - Analytics Domain Provider

Implements Firebase/Mixpanel integration, event batching, and persistence. Second in the analytics domain chain (2/6).

## Usage
```
/analytics-provider
```

## Parameters
- None. This skill consumes analytics-schema outputs and produces provider artifacts.

## What It Does
1. Integrates **Firebase Analytics** or **Mixpanel** (logEvent, setUserProperties)
2. Implements **AnalyticsRepository** — domain-facing repository interface
3. Implements **AnalyticsRemoteDataSource** — Firebase/Mixpanel client wrapper
4. Implements **event batching** — buffer events, flush on threshold or timer
5. Implements **AnalyticsLocalDataSource** — Hive persistence for offline queue
6. Handles **user identification** — anonymous ID, user ID when authenticated

## Output
- `analytics_repository.dart` — AnalyticsRepository implementation
- `analytics_remote_data_source.dart` — Firebase/Mixpanel client wrapper
- `analytics_local_data_source.dart` — Hive persistence for offline events
- Event batching utilities

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (analytics-schema responsibility)
- Write flow/state orchestration (analytics-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Firebase Analytics or Mixpanel
- **Storage:** Hive (offline event queue)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** analytics (TaskSpec domain)
