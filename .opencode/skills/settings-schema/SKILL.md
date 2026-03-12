---
name: settings-schema
description: Define preference, app config, and type IDs 110–119 for the settings domain
---

# settings-schema - Settings Domain Schema

Defines preference, app config, and settings state types for the settings domain. First in the settings domain chain (1/6).

## Usage
```
/settings-schema
```

## Parameters
- None. This skill produces schema artifacts for the settings domain.

## What It Does
1. Defines **Preference** entity with Hive persistence (`@HiveType` typeId: 110)
2. Defines **AppConfig** model with Hive persistence (typeId: 111)
3. Defines **FeatureFlag** model with Hive persistence (typeId: 112)
4. Creates **PreferenceDTO**, **AppConfigDTO** for API/transport layer
5. Creates **PreferenceValidator** for input validation
6. Defines preference types (boolean, string, number, enum)

## Output
- `preference.dart` — Preference model with `@HiveType(typeId: 110)`
- `app_config.dart` — AppConfig model with `@HiveType(typeId: 111)`
- `feature_flag.dart` — FeatureFlag model with `@HiveType(typeId: 112)`
- `preference_dto.dart` — Preference DTO for API/transport
- `app_config_dto.dart` — AppConfig DTO for API/transport
- `preference_validator.dart` — Preference input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** settings (TaskSpec domain)
