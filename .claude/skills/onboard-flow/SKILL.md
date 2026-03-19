---
name: onboard-flow
description: Implement onboarding step progression, skip logic, and conditional paths with Riverpod
---

# onboard-flow - Onboarding Domain Flow

Implements step progression, skip logic, and conditional paths for the onboarding flow with Riverpod. Third in the onboarding domain chain (3/6).

## Usage
```
/onboard-flow
```

## Parameters
- None. This skill consumes onboard-schema and onboard-provider outputs and produces flow artifacts.

## What It Does
1. Implements **OnboardingNotifier** — Riverpod StateNotifier for onboarding step state
2. Defines **step state** — current step index, completed steps, skipped steps, in-progress
3. Implements **step progression logic** — next, previous, jump-to-step, complete-step
4. Implements **skip logic** — conditional step skipping based on user choices or state
5. Implements **conditional paths** — branch flows (e.g., new user vs returning, feature flags)
6. Registers **onboardProvider** — Riverpod provider exposing OnboardingNotifier
7. Handles **completion state** — mark onboarding complete, persist completion flag
8. Coordinates with **onboard-provider** — load/save step state, completion status

## Output
- `onboarding_notifier.dart` — OnboardingNotifier (StateNotifier<OnboardingState>)
- `onboarding_state.dart` — OnboardingState with step index, completed/skipped steps
- `onboard_provider.dart` — onboardProvider (Riverpod Provider)
- `step_progression.dart` — progression logic (next, previous, skip, conditional branches)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (onboard-schema responsibility)
- Write repository or data source code (onboard-provider responsibility)
- Write UI components or screens (onboard-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (step state, completion flag, via onboard-provider)
- **Backend:** Supabase (via onboard-provider repository, if needed)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** onboard (TaskSpec domain)
