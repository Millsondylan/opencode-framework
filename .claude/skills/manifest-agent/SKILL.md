---
name: manifest-agent
description: Final app manifest — every screen, route, service, model, provider, test
---

# manifest-agent - App Manifest Generator

Produces final app manifest: every screen, route, service, model, provider, and test. Single source of truth for app structure.

## Usage
```
/manifest-agent
```

## Parameters
- **Scope** — App root or config (default: full app)
- **Include** — Optional filters (screens only, routes only, etc.)

## What It Does
1. Discovers all screens and their routes
2. Lists services (API, storage, auth, etc.)
3. Lists models/entities
4. Lists providers (Riverpod, Bloc, etc.)
5. Lists tests and coverage mapping
6. Produces structured JSON manifest

## Output
- `app-manifest.json` — Screens, routes, services, models, providers, tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Modify source code (read-only discovery)
- Omit dynamic or generated routes when discoverable
- Include sensitive config (keys, URLs) in manifest
