---
name: notif-test
description: Write mock push tests, local notification tests, and test suite for the notifications domain
---

# notif-test - Notifications Domain Test

Writes mock push tests, local notification tests, and the full test suite for the notifications domain. Sixth in the notifications domain chain (6/6).

## Usage
```
/notif-test
```

## Parameters
- None. This skill consumes all prior notifications domain outputs and produces test artifacts.

## What It Does
1. Writes **mock push tests** — simulates FCM/APNs payloads, tests handler logic in isolation
2. Writes **local notification tests** — tests scheduling, display, and cancellation of local notifications
3. Writes **unit tests** for notification logic (validators, guards, rate limiter, quiet hours)
4. Writes **widget tests** for notification UI (preference screens, permission prompts)
5. Provides **mock FCM/APNs clients** for isolated testing
6. Achieves **>80% coverage** for notifications domain code
7. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `notification_validator_test.dart` — Unit tests for NotificationValidator
- `notification_guard_test.dart` — Unit tests for NotificationGuard
- `notification_rate_limiter_test.dart` — Unit tests for rate limiting
- `notification_quiet_hours_test.dart` — Unit tests for quiet hours
- `mock_fcm_client.dart` — Mock FCM client for push tests
- `local_notification_test.dart` — Tests for local notification scheduling/display
- `notification_repository_test.dart` — Unit tests for NotificationRepository (mocked data source)
- `notification_integration_test.dart` — Integration tests for notification flows

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production notification logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock FCM/APNs clients
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** notifications (TaskSpec domain)
