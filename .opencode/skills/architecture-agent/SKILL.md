---
name: architecture-agent
description: Decides app structure — Clean Architecture layers, feature-first layout
---

# architecture-agent - App Architecture

Decides application structure with Clean Architecture layers and feature-first layout. Defines the foundational directory structure and architectural contract.

## Usage
```
/architecture-agent
```

## Parameters
- None. This skill produces architecture artifacts for the project.

## What It Does
1. Defines **Clean Architecture** layers (domain, data, presentation)
2. Establishes **feature-first** layout
3. Creates **lib/** structure with core and features
4. Defines **test/** mirror structure
5. Creates **lib/core/** for shared infrastructure
6. Creates **lib/features/** for domain features
7. Defines **main.dart** entry point
8. Defines **app.dart** root widget
9. Creates **failures.dart** for error handling
10. Outputs **architecture-contract.yaml** documenting the structure

## Output
- `lib/` — Root library structure
- `test/` — Test directory mirror
- `lib/core/` — Shared core infrastructure
- `lib/features/` — Feature modules
- `main.dart` — Application entry point
- `app.dart` — Root widget
- `failures.dart` — Failure/error types
- `architecture-contract.yaml` — Architecture documentation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write tests
- Create UI components

## Tech Stack
- **Architecture:** Clean Architecture
- **Layout:** Feature-first
- **Platform:** Flutter/Dart (mobile)
