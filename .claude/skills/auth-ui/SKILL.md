---
name: auth-ui
description: Implement login, register, forgot password, MFA screens with Material 3; form validation and error states
---

# auth-ui - Auth Domain UI

Implements auth screens with Material 3: login, registration, forgot password, MFA, and profile. Fourth in the auth domain chain (4/6).

## Usage
```
/auth-ui
```

## Parameters
- None. This skill consumes auth-flow outputs and produces UI artifacts.

## What It Does
1. Implements **LoginScreen** — email/password form, submit, loading state
2. Implements **RegisterScreen** — sign-up form, validation, submit
3. Implements **ForgotPasswordScreen** — email input, reset request
4. Implements **MfaScreen** — OTP/code input, verify, retry
5. Implements **ProfileScreen** — user info display, sign-out action
6. Adds **form validation UI** — inline errors, field-level feedback
7. Handles **error states** — snackbars, banners, inline error messages
8. Uses **Material 3** — components, theming, typography

## Output
- `login_screen.dart` — LoginScreen widget
- `register_screen.dart` — RegisterScreen widget
- `forgot_password_screen.dart` — ForgotPasswordScreen widget
- `mfa_screen.dart` — MfaScreen widget
- `profile_screen.dart` — ProfileScreen widget
- Form validation UI components (e.g., validated text fields)
- Error state widgets (snackbar, banner, inline)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (auth-schema responsibility)
- Write repository or data source code (auth-provider responsibility)
- Write flow/state orchestration (auth-flow responsibility)
- Write route guards or auth middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read authProvider, call AuthNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** auth (TaskSpec domain)
