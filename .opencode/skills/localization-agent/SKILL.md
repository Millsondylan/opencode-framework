---
name: localization-agent
description: ARB files, l10n setup, intl, RTL scaffolding
---

# localization-agent - Localization (l10n)

Configures ARB files, l10n setup, intl, and RTL scaffolding. Produces localization infrastructure.

## Usage
```
/localization-agent
```

## Parameters
- None. This skill produces localization artifacts.

## What It Does
1. Sets up **ARB files** (Application Resource Bundle)
2. Configures **l10n** (Flutter gen-l10n)
3. Integrates **intl** for formatting (dates, numbers)
4. Adds **RTL scaffolding** (right-to-left support)
5. Outputs **lib/l10n/** — generated and source l10n
6. Outputs **ARB files** — translation source files
7. Outputs **AppLocalizations delegate** — l10n access

## Output
- `lib/l10n/` — Localization module
- ARB files — translation source files
- AppLocalizations delegate — generated l10n access

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)

## Tech Stack
- **l10n:** Flutter gen-l10n, ARB
- **Formatting:** intl
- **RTL:** Directionality, RTL layout support
