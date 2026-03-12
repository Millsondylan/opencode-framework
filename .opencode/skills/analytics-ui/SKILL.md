---
name: analytics-ui
description: Implement debug overlay, consent UI, and analytics dashboard for the analytics domain
---

# analytics-ui - Analytics Domain UI

Implements debug overlay, consent UI, and analytics dashboard. Fourth in the analytics domain chain (4/6).

## Usage
```
/analytics-ui
```

## Parameters
- None. This skill consumes analytics-flow outputs and produces UI artifacts.

## What It Does
1. Implements **AnalyticsDebugOverlay** — shows recent events in dev/debug mode
2. Implements **ConsentScreen** — analytics consent prompt, accept/decline
3. Implements **AnalyticsDashboard** — optional in-app event summary (admin)
4. Handles **consent state** — banner, modal, settings link
5. Uses **Material 3** — components, theming, typography

## Output
- `analytics_debug_overlay.dart` — AnalyticsDebugOverlay widget
- `consent_screen.dart` — ConsentScreen widget
- `analytics_dashboard.dart` — AnalyticsDashboard widget (optional)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (analytics-schema responsibility)
- Write repository or data source code (analytics-provider responsibility)
- Write flow/state orchestration (analytics-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read analyticsProvider, call AnalyticsNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** analytics (TaskSpec domain)
