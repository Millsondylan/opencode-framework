---
name: onboard-guard
description: Implement first-launch detection, version-based re-onboarding, and OnboardingGuard for the onboarding domain
---

# onboard-guard - Onboarding Domain Guard

Implements first-launch detection, version-based re-onboarding, and OnboardingGuard. Fifth in the onboarding domain chain (5/6).

## Usage
```
/onboard-guard
```

## Parameters
- None. This skill consumes onboard-schema, onboard-provider, and onboard-flow outputs and produces guard artifacts.

## What It Does
1. Implements **OnboardingGuard** — determines whether to show onboarding (first launch, version upgrade, or skip)
2. Implements **first-launch detection** — detects app first run and triggers onboarding flow
3. Implements **version-based re-onboarding** — re-shows onboarding when app version changes (e.g., major/minor bump)
4. Integrates with Riverpod onboarding state and Hive persistence for guard decisions
5. Handles redirect/skip flows when guard determines onboarding is not needed
6. Coordinates with onboard-provider for progress/completion checks and version tracking

## Output
- `onboarding_guard.dart` — OnboardingGuard for first-launch and version-based decisions
- `first_launch_detector.dart` — First-launch detection logic
- `version_onboarding_checker.dart` — Version-based re-onboarding logic

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (onboard-schema responsibility)
- Write provider/repository code (onboard-provider responsibility)
- Write flow/state orchestration (onboard-flow responsibility)
- Write UI components or screens (onboard-ui responsibility)
- Write tests (onboard-test responsibility)

## Tech Stack
- **State:** Riverpod (reads onboarding state for guard decisions)
- **Storage:** Hive (first-launch flag, last-seen version, completion persistence)
- **Backend:** Supabase (optional version sync)
- **UI:** Material 3 (navigation integration)
- **Architecture:** Clean Architecture (presentation/guard layer)
- **Domain:** onboarding (TaskSpec domain)
- **Shared:** Riverpod, Hive, Supabase, Material 3, Clean Architecture
