---
name: di-agent
description: Riverpod DI — provider tree, service registration, wiring repositories
---

# di-agent - Dependency Injection

Configures Riverpod dependency injection — provider tree, service registration, and repository wiring. Does not implement repository logic.

## Usage
```
/di-agent
```

## Parameters
- None. This skill produces DI artifacts for the project.

## What It Does
1. Creates **provider tree** structure
2. Registers **services** in Riverpod
3. Wires **repositories** to providers (interfaces only, no impl)
4. Configures **Supabase/API client** providers
5. Outputs **core_providers.dart** — core/shared providers
6. Outputs **repository_providers.dart** — repository provider bindings
7. Outputs **service_providers.dart** — service registrations
8. Outputs Supabase/API client provider modules

## Output
- `core_providers.dart` — Core provider tree
- `repository_providers.dart` — Repository provider bindings
- `service_providers.dart` — Service registrations
- Supabase/API client provider modules

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository implementations
- Write UI components
- Write tests

## Tech Stack
- **DI:** Riverpod
- **Backend:** Supabase (optional)
- **Architecture:** Clean Architecture
