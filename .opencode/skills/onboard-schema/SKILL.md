---
name: onboard-schema
description: Define onboarding step models and user preference capture schema for the onboarding domain
---

# onboard-schema - Onboarding Domain Schema

Defines onboarding step models, user preference capture schema, and DTOs for the onboarding domain. First in the onboarding domain chain (1/6).

## Usage
```
/onboard-schema
```

## Parameters
- None. This skill produces schema artifacts for the onboarding domain.

## What It Does
1. Defines **OnboardingStep** entity/enum with Hive persistence (`@HiveType` typeId: 50)
2. Defines **UserPreference** model for captured preferences with Hive persistence (typeId: 51)
3. Defines **OnboardingProgress** model with Hive persistence (typeId: 52)
4. Creates **OnboardingStepDTO**, **UserPreferenceDTO**, **OnboardingProgressDTO** for API/transport layer
5. Creates **UserPreferenceValidator** for input validation
6. Defines onboarding state types (welcome, preferences, complete, skipped)

## Output
- `onboarding_step.dart` — OnboardingStep model/enum with `@HiveType(typeId: 50)`
- `user_preference.dart` — UserPreference model with `@HiveType(typeId: 51)`
- `onboarding_progress.dart` — OnboardingProgress model with `@HiveType(typeId: 52)`
- `onboarding_step_dto.dart` — OnboardingStep DTO for API/transport
- `user_preference_dto.dart` — UserPreference DTO for API/transport
- `onboarding_progress_dto.dart` — OnboardingProgress DTO for API/transport
- `user_preference_validator.dart` — User preference input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write flow logic
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** onboarding (TaskSpec domain)
- **Shared:** Riverpod, Hive, Supabase, Material 3, Clean Architecture
