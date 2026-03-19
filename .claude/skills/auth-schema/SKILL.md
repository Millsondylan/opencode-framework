---
name: auth-schema
description: Define auth data models and types for the authentication domain
---

# auth-schema - Auth Domain Schema

Defines the User model, token models, role enums, and auth state types for the authentication domain. First in the auth domain chain (1/6).

## Usage
```
/auth-schema
```

## Parameters
- None. This skill produces schema artifacts for the auth domain.

## What It Does
1. Defines the **User** entity with Hive persistence (`@HiveType` typeId: 10)
2. Defines **AuthToken** model with Hive persistence (typeId: 11)
3. Defines **Role** enum with Hive persistence (typeId: 12)
4. Creates **UserDTO** and **AuthTokenDTO** for API/transport layer
5. Creates **UserValidator** for input validation
6. Defines auth state types (signed-in, signed-out, loading, error)

## Output
- `user_entity.dart` — User model with `@HiveType(typeId: 10)`
- `auth_token.dart` — Token model with `@HiveType(typeId: 11)`
- `role.dart` — Role enum with `@HiveType(typeId: 12)`
- `user_dto.dart` — User DTO for API/transport
- `auth_token_dto.dart` — Auth token DTO for API/transport
- `user_validator.dart` — User input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** auth (TaskSpec domain)
