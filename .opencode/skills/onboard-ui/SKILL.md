---
name: onboard-ui
description: Implement welcome screens, tutorials, and permission request UI with Material 3
---

# onboard-ui - Onboarding Domain UI

Implements welcome screens, tutorials, and permission request UI with Material 3. Fourth in the onboarding domain chain (4/6).

## Usage
```
/onboard-ui
```

## Parameters
- None. This skill consumes onboard-flow outputs and produces UI artifacts.

## What It Does
1. Implements **WelcomeScreen** — first-run welcome, app value proposition, get-started CTA
2. Implements **tutorial screens** — step-by-step feature walkthrough, swipeable pages, progress indicator
3. Implements **permission request UI** — rationale copy, request CTA, link to app settings when denied
4. Adds **step navigation UI** — next, back, skip buttons; step indicator dots or progress bar
5. Handles **loading and transition states** — between steps, during permission requests
6. Handles **error states** — snackbars, banners for permission failures or flow errors
7. Uses **Material 3** — components, theming, typography

## Output
- `welcome_screen.dart` — WelcomeScreen widget
- `tutorial_screen.dart` — Tutorial/walkthrough screen with swipeable pages
- `onboarding_step_widget.dart` — Reusable step container with navigation
- `permission_request_screen.dart` — Permission rationale and request UI
- Step indicator / progress bar components
- Skip / next / back button components

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (onboard-schema responsibility)
- Write repository or data source code (onboard-provider responsibility)
- Write flow/state orchestration (onboard-flow responsibility)
- Write route guards or onboarding middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read onboardProvider, call OnboardingNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** onboard (TaskSpec domain)
