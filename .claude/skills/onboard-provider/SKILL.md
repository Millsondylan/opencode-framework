---
name: onboard-provider
description: Implement onboarding progress persistence, feature flags, and OnboardingRepository for the onboarding domain
---

# onboard-provider - Onboarding Domain Provider

Implements onboarding progress persistence, feature flags, and the onboarding repository layer. Second in the onboarding domain chain (2/6).

## Usage
```
/onboard-provider
```

## Parameters
- None. This skill consumes onboard-schema outputs and produces provider artifacts.

## What It Does
1. Implements **OnboardingRepository** — domain-facing repository interface
2. Implements **onboarding progress persistence** — Hive or local storage for step completion, last-seen step, completion timestamp
3. Implements **feature flags** — remote config or local flags for onboarding visibility (e.g., show onboarding for new users, A/B variants)
4. Implements **OnboardingLocalDataSource** — Hive/local cache for progress and preferences
5. Optionally integrates **Supabase** for syncing onboarding state across devices
6. Handles progress read/write, completion marking, and reset

## Output
- `onboarding_repository.dart` — OnboardingRepository implementation
- `onboarding_local_data_source.dart` — OnboardingLocalDataSource (Hive/local progress persistence)
- `onboarding_feature_flags.dart` — Feature flags for onboarding visibility and variants
- Progress persistence implementation (step completion, user preferences sync)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (onboard-schema responsibility)
- Write flow/state orchestration (onboard-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase (optional sync)
- **State:** Riverpod (provider registration only, not flow logic)
- **Storage:** Hive for progress and preference persistence
- **Architecture:** Clean Architecture (data layer)
- **Domain:** onboarding (TaskSpec domain)
- **Shared:** Riverpod, Hive, Supabase, Material 3, Clean Architecture
