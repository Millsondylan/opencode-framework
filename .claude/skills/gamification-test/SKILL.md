---
name: gamification-test
description: Write points calculation and badge criteria tests for the gamification domain
---

# gamification-test - Gamification Domain Test

Writes points calculation and badge criteria tests. Sixth in the gamification domain chain (6/6).

## Usage
```
/gamification-test
```

## Parameters
- None. This skill consumes all prior gamification domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for gamification logic (points, badges, guards)
2. Writes **points calculation tests** — add, deduct, balance
3. Writes **badge criteria tests** — criteria evaluation, award logic
4. Provides **mock gamification repository** for isolated testing
5. Achieves **>80% coverage** for gamification domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `points_repository_test.dart` — Unit tests for PointsRepository
- `badge_repository_test.dart` — Unit tests for BadgeRepository
- `gamification_notifier_test.dart` — Unit tests for GamificationNotifier
- `points_calculation_test.dart` — Points calculation tests
- `badge_criteria_test.dart` — Badge criteria tests
- `mock_gamification_repository.dart` — Mock gamification repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production gamification logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** gamification (TaskSpec domain)
