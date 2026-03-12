---
name: auth-provider
description: Implement Supabase Auth integration, repository, and secure token storage for the auth domain
---

# auth-provider - Auth Domain Provider

Implements Supabase Auth integration, repository layer, remote data source, and secure token storage. Second in the auth domain chain (2/6).

## Usage
```
/auth-provider
```

## Parameters
- None. This skill consumes auth-schema outputs and produces provider artifacts.

## What It Does
1. Integrates **Supabase Auth** (signUp, signIn, signOut, session)
2. Implements **AuthRepository** — domain-facing repository interface
3. Implements **AuthRemoteDataSource** — Supabase client wrapper
4. Implements **secure token storage** — encrypted storage for access/refresh tokens
5. Handles token refresh and session persistence
6. Supports OAuth providers (Google, Apple, etc.) via Supabase

## Output
- `auth_repository.dart` — AuthRepository implementation
- `auth_remote_data_source.dart` — AuthRemoteDataSource (Supabase Auth client)
- Secure token storage implementation (e.g., flutter_secure_storage or platform-specific)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (auth-schema responsibility)
- Write flow/state orchestration (auth-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase Auth
- **State:** Riverpod (provider registration only, not flow logic)
- **Storage:** flutter_secure_storage or equivalent for tokens
- **Architecture:** Clean Architecture (data layer)
- **Domain:** auth (TaskSpec domain)
