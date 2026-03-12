---
name: auth-test
description: Write unit tests for auth logic, widget tests for auth screens, mock Supabase client, and integration tests for the auth domain
---

# auth-test - Auth Domain Test

Writes unit tests for auth logic, widget tests for auth screens, mocks Supabase client, and integration tests. Sixth in the auth domain chain (6/6).

## Usage
```
/auth-test
```

## Parameters
- None. This skill consumes all prior auth domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for auth logic (validators, guards, middleware, token handling)
2. Writes **widget tests** for auth screens (login, signup, profile, biometric prompt)
3. Provides **mock Supabase client** for isolated testing
4. Writes **integration tests** for auth flows (sign-in, sign-out, session refresh)
5. Achieves **>80% coverage** for auth domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `auth_validator_test.dart` — Unit tests for UserValidator
- `auth_guard_test.dart` — Unit tests for AuthGuard
- `auth_repository_test.dart` — Unit tests for AuthRepository (mocked data source)
- `login_screen_test.dart` — Widget tests for login screen
- `signup_screen_test.dart` — Widget tests for signup screen
- `mock_supabase_client.dart` — Mock Supabase Auth client for tests
- `auth_integration_test.dart` — Integration tests for auth flows

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production auth logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase Auth client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** auth (TaskSpec domain)
