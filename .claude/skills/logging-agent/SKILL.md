---
name: logging-agent
description: Structured logging, Sentry/Crashlytics, analytics event schema
---

# logging-agent - Logging & Observability

Configures structured logging, Sentry/Crashlytics integration, and analytics event schema. Produces logging infrastructure.

## Usage
```
/logging-agent
```

## Parameters
- None. This skill produces logging artifacts.

## What It Does
1. Implements **structured logging** (levels, context, metadata)
2. Integrates **Sentry** for error tracking
3. Integrates **Crashlytics** for crash reporting
4. Defines **analytics event schema** (event names, params)
5. Outputs **lib/core/logging/** — logging module
6. Outputs **Logger service** — structured logger
7. Outputs **analytics schema** — event definitions

## Output
- `lib/core/logging/` — Logging module
- Logger service — structured logger implementation
- Analytics schema — event names and parameter definitions

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Include real API keys (use env vars)

## Tech Stack
- **Logging:** logger, structured logs
- **Errors:** Sentry
- **Crashes:** Firebase Crashlytics
- **Analytics:** Event schema
