---
name: settings-provider
description: Implement preference persistence and remote config for the settings domain
---

# settings-provider - Settings Domain Provider

Implements preference persistence and remote config. Second in the settings domain chain (2/6).

## Usage
```
/settings-provider
```

## Parameters
- None. This skill consumes settings-schema outputs and produces provider artifacts.

## What It Does
1. Implements **SettingsRepository** — domain-facing repository interface
2. Implements **PreferenceLocalDataSource** — Hive persistence for preferences
3. Implements **RemoteConfigDataSource** — Firebase Remote Config or Supabase
4. Handles **preference persistence** — get, set, sync
5. Handles **remote config** — fetch, cache, defaults
6. Supports **feature flags** — boolean flags, rollout percentages

## Output
- `settings_repository.dart` — SettingsRepository implementation
- `preference_local_data_source.dart` — Hive persistence for preferences
- `remote_config_data_source.dart` — Remote config client

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (settings-schema responsibility)
- Write flow/state orchestration (settings-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Firebase Remote Config or Supabase
- **Storage:** Hive (preference persistence)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** settings (TaskSpec domain)
