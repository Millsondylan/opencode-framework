---
name: search-guard
description: Implement query sanitization and result access control for the search domain
---

# search-guard - Search Domain Guard

Implements query sanitization and result access control. Fifth in the search domain chain (5/6).

## Usage
```
/search-guard
```

## Parameters
- None. This skill consumes search-schema, search-provider, and search-flow outputs and produces guard artifacts.

## What It Does
1. Implements **SearchGuard** — query sanitization (injection prevention, XSS, length limits, forbidden characters)
2. Implements **result access control** — filters results based on user permissions, entitlements, or visibility rules
3. Validates **query input** before it reaches the search provider (whitelist allowed operators, sanitize filter values)
4. Integrates with Riverpod search state for guard decisions
5. Handles redirect or block flows when guards fail (e.g., rate limit, forbidden query)
6. Coordinates with SearchRepository for server-side validation when needed

## Output
- `search_guard.dart` — SearchGuard for query sanitization and result access control
- `query_validator.dart` — Query validation logic (whitelist, sanitization, length limits)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (search-schema responsibility)
- Write provider/repository code (search-provider responsibility)
- Write flow/state orchestration (search-flow responsibility)
- Write UI components or screens (search-ui responsibility)
- Write tests (search-test responsibility)

## Tech Stack
- **State:** Riverpod (reads search state for guard decisions)
- **Storage:** Hive (query history, rate limit metadata if needed)
- **Backend:** Supabase (via search-provider for server-side validation)
- **UI:** Material 3 (navigation integration)
- **Architecture:** Clean Architecture (presentation/guard layer)
- **Domain:** search (TaskSpec domain)
