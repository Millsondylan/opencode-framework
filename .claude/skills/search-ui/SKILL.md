---
name: search-ui
description: Implement search bar, results list, filter sheet, empty states with Material 3
---

# search-ui - Search Domain UI

Implements search bar, results list, filter sheet, and empty states with Material 3. Fourth in the search domain chain (4/6).

## Usage
```
/search-ui
```

## Parameters
- None. This skill consumes search-flow outputs and produces UI artifacts.

## What It Does
1. Implements **SearchBar** — text field, clear button, submit, loading indicator
2. Implements **SearchResultsScreen** — results list/grid, item cards, tap navigation
3. Implements **filter sheet** — bottom sheet or drawer for filter options (category, date, etc.)
4. Handles **empty states** — no results, no query yet, error state UI
5. Adds **pagination UI** — load more button or infinite scroll indicator
6. Handles **loading states** — shimmer, skeleton, or spinner for results
7. Uses **Material 3** — components, theming, typography

## Output
- `search_bar.dart` — SearchBar widget
- `search_results_screen.dart` — SearchResultsScreen widget
- `filter_sheet.dart` — Filter sheet/bottom sheet widget
- Empty state widgets (no results, no query, error)
- Pagination UI components (load more, infinite scroll)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (search-schema responsibility)
- Write repository or data source code (search-provider responsibility)
- Write flow/state orchestration (search-flow responsibility)
- Write route guards or search middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read searchProvider, call SearchNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** search (TaskSpec domain)
