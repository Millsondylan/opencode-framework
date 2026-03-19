---
name: router-agent
description: GoRouter with deep links, route guards, redirect rules, shell routes
---

# router-agent - Navigation & Routing

Configures GoRouter with deep links, route guards, redirect rules, and shell routes. Defines the navigation structure.

## Usage
```
/router-agent
```

## Parameters
- None. This skill produces routing artifacts for the project.

## What It Does
1. Configures **GoRouter** with route definitions
2. Sets up **deep links** (web URLs, app links)
3. Implements **route guards** (auth, permissions)
4. Defines **redirect rules** (e.g., unauthenticated → login)
5. Configures **shell routes** (nested navigation, bottom nav)
6. Outputs **router.dart** — main router config
7. Outputs **route_names.dart** — route name constants
8. Outputs **route_guards.dart** — guard logic
9. Outputs **route manifest** — route documentation

## Output
- `router.dart` — GoRouter configuration
- `route_names.dart` — Route name constants
- `route_guards.dart` — Route guard implementations
- Route manifest (documentation)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)

## Tech Stack
- **Routing:** GoRouter
- **Platform:** Flutter/Dart (mobile)
