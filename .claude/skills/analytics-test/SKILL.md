---
name: analytics-test
description: Write mock analytics, event tests, and consent tests for the analytics domain
---

# analytics-test - Analytics Domain Test

Writes mock analytics, event tests, and consent tests. Sixth in the analytics domain chain (6/6).

## Usage
```
/analytics-test
```

## Parameters
- None. This skill consumes all prior analytics domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for analytics logic (PII scrubber, consent guard, event validation)
2. Provides **mock analytics repository** for isolated testing
3. Writes **event tests** — event dispatch, batching, flush
4. Writes **consent tests** — consent flow, guard behavior
5. Achieves **>80% coverage** for analytics domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `analytics_repository_test.dart` — Unit tests for AnalyticsRepository
- `analytics_notifier_test.dart` — Unit tests for AnalyticsNotifier
- `pii_scrubber_test.dart` — PII scrubber tests
- `consent_guard_test.dart` — Consent guard tests
- `mock_analytics_repository.dart` — Mock analytics repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production analytics logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Firebase/Mixpanel client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** analytics (TaskSpec domain)
