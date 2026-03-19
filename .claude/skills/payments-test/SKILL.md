---
name: payments-test
description: Write sandbox purchase tests, mock billing, entitlement tests, and integration tests for the payments domain
---

# payments-test - Payments Domain Test

Writes sandbox purchase tests, mock billing, entitlement tests, and integration tests for the payments domain. Sixth in the payments domain chain (6/6).

## Usage
```
/payments-test
```

## Parameters
- None. This skill consumes all prior payments domain outputs and produces test artifacts.

## What It Does
1. Writes **sandbox purchase tests** — simulates purchase flows in sandbox/test environment
2. Provides **mock billing** — mock RevenueCat, Stripe, or Google Play Billing client for isolated testing
3. Writes **entitlement tests** — unit tests for EntitlementGuard, entitlement checks, access control
4. Writes **purchase verification tests** — receipt validation, subscription status, fraud check logic
5. Writes **integration tests** — purchase flow, restore purchases, paywall → purchase → entitlement
6. Achieves **>80% coverage** for payments domain code
7. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `entitlement_guard_test.dart` — Unit tests for EntitlementGuard
- `purchase_verification_test.dart` — Unit tests for purchase verification logic
- `fraud_check_test.dart` — Unit tests for FraudCheck
- `payments_repository_test.dart` — Unit tests for PaymentsRepository (mocked data source)
- `payments_notifier_test.dart` — Unit tests for PaymentsNotifier / flow state
- `mock_billing_client.dart` — Mock RevenueCat/Stripe/Play Billing client for tests
- `paywall_screen_test.dart` — Widget tests for paywall screen
- `payments_integration_test.dart` — Integration tests for purchase flows

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production payments logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Billing Mock:** Mock RevenueCat, Stripe, or Google Play Billing client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** payments (TaskSpec domain)
