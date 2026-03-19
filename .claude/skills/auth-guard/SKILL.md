---
name: auth-guard
description: Implement route guards, session expiry detection, biometric authentication, and permission checks for the auth domain
---

# auth-guard - Auth Domain Guard

Implements route guards, session expiry detection, biometric authentication, and permission checks. Fifth in the auth domain chain (5/6).

## Usage
```
/auth-guard
```

## Parameters
- None. This skill consumes auth-schema and auth-provider outputs and produces guard artifacts.

## What It Does
1. Implements **AuthGuard** — route/navigation guards that block unauthenticated access
2. Implements **SessionMiddleware** — detects session expiry and triggers re-auth or token refresh
3. Implements **BiometricLock** — biometric authentication (Face ID, Touch ID, fingerprint)
4. Implements **permission checks** — role-based and capability-based access control
5. Integrates with Riverpod auth state for guard decisions
6. Handles redirect flows when guards fail (e.g., to login screen)

## Output
- `auth_guard.dart` — AuthGuard for route protection
- `session_middleware.dart` — SessionMiddleware for expiry detection
- `biometric_lock.dart` — BiometricLock for biometric auth

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (auth-schema responsibility)
- Write provider/repository code (auth-provider responsibility)
- Write flow/state orchestration (auth-flow responsibility)
- Write UI components or screens
- Write tests (auth-test responsibility)

## Tech Stack
- **State:** Riverpod (reads auth state for guard decisions)
- **Storage:** Hive (session persistence)
- **Backend:** Supabase (session validation)
- **UI:** Material 3 (navigation integration)
- **Architecture:** Clean Architecture (presentation/guard layer)
- **Domain:** auth (TaskSpec domain)
