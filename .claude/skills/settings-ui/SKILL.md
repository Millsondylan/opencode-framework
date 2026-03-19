---
name: settings-ui
description: Implement SettingsScreen, toggles, and account section for the settings domain
---

# settings-ui - Settings Domain UI

Implements SettingsScreen, toggles, and account section. Fourth in the settings domain chain (4/6).

## Usage
```
/settings-ui
```

## Parameters
- None. This skill consumes settings-flow outputs and produces UI artifacts.

## What It Does
1. Implements **SettingsScreen** — grouped settings, sections
2. Implements **PreferenceToggle** — SwitchListTile, preference binding
3. Implements **AccountSection** — profile, logout, delete account
4. Implements **ThemeSelector** — light/dark/system preference
5. Handles **loading and error states**
6. Uses **Material 3** — components, theming, typography

## Output
- `settings_screen.dart` — SettingsScreen widget
- `preference_toggle.dart` — PreferenceToggle widget
- `account_section.dart` — AccountSection widget
- `theme_selector.dart` — ThemeSelector widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (settings-schema responsibility)
- Write repository or data source code (settings-provider responsibility)
- Write flow/state orchestration (settings-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read settingsProvider, call SettingsNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** settings (TaskSpec domain)
