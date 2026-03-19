---
name: env-config-agent
description: .env structures, dart-define, flavor setup (dev/staging/prod). No hardcoded secrets.
---

# env-config-agent - Environment Configuration

Configures environment structures, dart-define, and flavor setup for dev/staging/prod. Ensures no hardcoded secrets — uses env vars and secure patterns.

## Usage
```
/env-config-agent
```

## Parameters
- None. This skill produces environment config artifacts.

## What It Does
1. Creates **.env structures** for each environment
2. Configures **dart-define** for build-time env injection
3. Sets up **flavor configuration** (dev, staging, prod)
4. Ensures **no hardcoded secrets** — placeholders and env var references only
5. Outputs **.env.development** — dev env template
6. Outputs **.env.staging** — staging env template
7. Outputs **.env.production** — prod env template
8. Outputs **flavor config** — build flavor definitions

## Output
- `.env.development` — Development environment template
- `.env.staging` — Staging environment template
- `.env.production` — Production environment template
- Flavor config — dev/staging/prod build configuration

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Include real credentials or secrets (placeholders only)

## Tech Stack
- **Env:** dart-define, --dart-define-from-file
- **Flavors:** Flutter flavors
- **Platform:** Flutter/Dart (mobile)
