---
name: search-test
description: Write mock search provider, pagination tests, and integration tests for the search domain
---

# search-test - Search Domain Test

Writes mock search provider, pagination tests, and integration tests for the search domain. Sixth in the search domain chain (6/6).

## Usage
```
/search-test
```

## Parameters
- None. This skill consumes all prior search domain outputs and produces test artifacts.

## What It Does
1. Provides **mock search provider** — mock Algolia, Meilisearch, or SearchRepository for isolated testing
2. Writes **pagination tests** — unit tests for load more, cursor/offset handling, hasNext page logic
3. Writes **SearchGuard tests** — unit tests for query sanitization, result access control, validation
4. Writes **SearchNotifier tests** — unit tests for debounce, filter application, state transitions
5. Writes **integration tests** — search flow (query → results → pagination → filter)
6. Achieves **>80% coverage** for search domain code
7. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `mock_search_provider.dart` — Mock SearchRepository / Algolia / Meilisearch client for tests
- `search_guard_test.dart` — Unit tests for SearchGuard and query validation
- `search_notifier_test.dart` — Unit tests for SearchNotifier (debounce, pagination, filters)
- `pagination_test.dart` — Unit tests for pagination logic (load more, hasNext, cursor)
- `search_integration_test.dart` — Integration tests for search flows

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production search logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Search Mock:** Mock Algolia, Meilisearch, or SearchRepository
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** search (TaskSpec domain)
