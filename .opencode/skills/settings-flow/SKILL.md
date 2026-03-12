---
name: settings-flow
description: Implement preference state and feature flags for the settings domain
---

# settings-flow - Settings Domain Flow

Implements preference state and feature flags. Third in the settings domain chain (3/6).

## Usage
```
/settings-flow
```

## Parameters
- None. This skill consumes settings-schema and settings-provider outputs and produces flow artifacts.

## What It Does
1. Implements **SettingsNotifier** — Riverpod StateNotifier for settings state
2. Defines **SettingsState** — preferences, config, flags, loading, error
3. Registers **settingsProvider**, **preferenceProvider**, **featureFlagProvider**
4. Orchestrates **preference state** — load, update, persist
5. Orchestrates **feature flags** — fetch, cache, evaluate
6. Handles **config sync** — remote config refresh

## Output
- `settings_notifier.dart` — SettingsNotifier (StateNotifier<SettingsState>)
- `settings_state.dart` — SettingsState sealed class / union type
- `settings_provider.dart` — settingsProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (settings-schema responsibility)
- Write repository or data source code (settings-provider responsibility)
- Write UI components or screens (settings-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (preference persistence via provider)
- **Backend:** Firebase Remote Config or Supabase (via settings-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** settings (TaskSpec domain)
