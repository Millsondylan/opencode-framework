---
name: onboard-test
description: Write flow progression tests, skip logic tests, and test suite for the onboarding domain
---

# onboard-test - Onboarding Domain Test

Writes flow progression tests, skip logic tests, and the full test suite for onboarding. Sixth in the onboarding domain chain (6/6).

## Usage
```
/onboard-test
```

## Parameters
- None. This skill consumes all prior onboarding domain outputs and produces test artifacts.

## What It Does
1. Writes **flow progression tests** — step advancement, next/previous, jump-to-step, completion
2. Writes **skip logic tests** — conditional step skipping based on user choices or state
3. Writes **unit tests** for OnboardingGuard, first-launch detection, version-based re-onboarding
4. Writes **widget tests** for onboarding screens (welcome, preferences, completion)
5. Provides **mock OnboardingRepository** and **mock Riverpod overrides** for isolated testing
6. Achieves **>80% coverage** for onboarding domain code
7. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `onboarding_notifier_test.dart` — Unit tests for OnboardingNotifier (flow progression)
- `step_progression_test.dart` — Unit tests for step progression and skip logic
- `onboarding_guard_test.dart` — Unit tests for OnboardingGuard, first-launch, version checks
- `onboarding_screen_test.dart` — Widget tests for onboarding screens
- `mock_onboarding_repository.dart` — Mock OnboardingRepository for tests
- `onboarding_integration_test.dart` — Integration tests for onboarding flows

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production onboarding logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **State Mock:** Mock Riverpod overrides
- **Repository Mock:** Mock OnboardingRepository
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** onboarding (TaskSpec domain)
- **Shared:** Riverpod, Hive, Supabase, Material 3, Clean Architecture
