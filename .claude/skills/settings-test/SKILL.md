---
name: settings-test
description: Write preference persistence and feature flag tests for the settings domain
---

# settings-test - Settings Domain Test

Writes preference persistence and feature flag tests. Sixth in the settings domain chain (6/6).

## Usage
```
/settings-test
```

## Parameters
- None. This skill consumes all prior settings domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for settings logic (validators, guards, migration)
2. Writes **preference persistence tests** — get, set, sync
3. Writes **feature flag tests** — fetch, evaluate, cache
4. Provides **mock settings repository** for isolated testing
5. Achieves **>80% coverage** for settings domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `settings_repository_test.dart` — Unit tests for SettingsRepository
- `settings_notifier_test.dart` — Unit tests for SettingsNotifier
- `preference_persistence_test.dart` — Preference persistence tests
- `feature_flag_test.dart` — Feature flag tests
- `mock_settings_repository.dart` — Mock settings repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production settings logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Remote Config client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** settings (TaskSpec domain)
