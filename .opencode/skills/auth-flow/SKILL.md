---
name: auth-flow
description: Implement auth state management with Riverpod; login, registration, MFA flows; session tracking
---

# auth-flow - Auth Domain Flow

Implements auth state management with Riverpod, orchestrates login, registration, and MFA flows, and tracks session state. Third in the auth domain chain (3/6).

## Usage
```
/auth-flow
```

## Parameters
- None. This skill consumes auth-schema and auth-provider outputs and produces flow artifacts.

## What It Does
1. Implements **AuthNotifier** — Riverpod StateNotifier for auth state
2. Defines **AuthState** — signed-in, signed-out, loading, error, MFA-pending
3. Registers **authProvider** — Riverpod provider exposing AuthNotifier
4. Orchestrates **login flow** — credentials → validation → provider sign-in
5. Orchestrates **registration flow** — sign-up → email verification (if required)
6. Orchestrates **MFA flow** — challenge → verify → session
7. Tracks **session** — persistence, refresh, expiry handling
8. Handles **sign-out** — clear session, reset state

## Output
- `auth_notifier.dart` — AuthNotifier (StateNotifier<AuthState>)
- `auth_state.dart` — AuthState sealed class / union type
- `auth_provider.dart` — authProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (auth-schema responsibility)
- Write repository or data source code (auth-provider responsibility)
- Write UI components or screens (auth-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (session metadata, if needed)
- **Backend:** Supabase (via auth-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** auth (TaskSpec domain)
