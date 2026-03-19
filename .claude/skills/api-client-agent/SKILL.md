---
name: api-client-agent
description: Dio/http client — interceptors (auth, logging, retry), token refresh
---

# api-client-agent - API Client

Configures Dio/http client with interceptors (auth, logging, retry) and token refresh. Produces API client infrastructure.

## Usage
```
/api-client-agent
```

## Parameters
- None. This skill produces API client artifacts.

## What It Does
1. Configures **Dio** (or http) client
2. Adds **auth interceptor** — Bearer token injection
3. Adds **logging interceptor** — request/response logging
4. Adds **retry interceptor** — exponential backoff retry
5. Implements **token refresh** — refresh on 401, retry original
6. Outputs **lib/core/api/** — API module
7. Outputs **Dio config** — base URL, timeouts, headers
8. Outputs **auth interceptor** — token injection
9. Outputs **retry interceptor** — retry logic

## Output
- `lib/core/api/` — API client module
- Dio config — client configuration
- Auth interceptor — token injection
- Retry interceptor — retry logic

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Include real tokens or secrets (use providers/env)

## Tech Stack
- **HTTP:** Dio
- **Auth:** Bearer token, refresh flow
- **Architecture:** Clean Architecture (data layer)
