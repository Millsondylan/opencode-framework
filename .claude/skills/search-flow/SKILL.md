---
name: search-flow
description: Implement search state management with Riverpod; debounce, pagination, filter application
---

# search-flow - Search Domain Flow

Implements search state management with Riverpod, debounce logic, pagination, and filter application. Third in the search domain chain (3/6).

## Usage
```
/search-flow
```

## Parameters
- None. This skill consumes search-schema and search-provider outputs and produces flow artifacts.

## What It Does
1. Implements **SearchNotifier** — Riverpod StateNotifier for search state
2. Defines **SearchState** — idle, loading, results, empty, error, paginating
3. Registers **searchProvider** — Riverpod provider exposing SearchNotifier
4. Implements **debounce** — query input debouncing (e.g., 300–500ms) before search execution
5. Implements **pagination logic** — load more, cursor-based or offset-based, hasNext page handling
6. Applies **filter application** — filter state → query params → provider trigger

## Output
- `search_notifier.dart` — SearchNotifier (StateNotifier<SearchState>)
- `search_state.dart` — SearchState sealed class / union type
- `search_provider.dart` — searchProvider (Riverpod Provider)
- Pagination logic (load more, next page, hasNext)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (search-schema responsibility)
- Write repository or data source code (search-provider responsibility)
- Write UI components or screens (search-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (search history, recent queries, if needed)
- **Backend:** Supabase (via search-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** search (TaskSpec domain)
