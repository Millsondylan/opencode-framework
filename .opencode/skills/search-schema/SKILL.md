---
name: search-schema
description: Define search index models, filter definitions, and result types for the search domain
---

# search-schema - Search Domain Schema

Defines search index models, filter definitions, result types, and search state types for the search domain. First in the search domain chain (1/6).

## Usage
```
/search-schema
```

## Parameters
- None. This skill produces schema artifacts for the search domain.

## What It Does
1. Defines **SearchIndex** entity with Hive persistence (`@HiveType` typeId: 40)
2. Defines **SearchFilter** model with Hive persistence (typeId: 41)
3. Defines **SearchResult** model with Hive persistence (typeId: 42)
4. Defines **SearchFacet** / **SearchSort** enums or models (typeIds: 43–44)
5. Creates **SearchIndexDTO**, **SearchFilterDTO**, **SearchResultDTO** for API/transport layer
6. Creates validators for search query and filter input validation
7. Defines search state types (idle, loading, results, error, empty)

## Output
- `search_index_entity.dart` — SearchIndex model with `@HiveType(typeId: 40)`
- `search_filter.dart` — SearchFilter model with `@HiveType(typeId: 41)`
- `search_result.dart` — SearchResult model with `@HiveType(typeId: 42)`
- `search_facet.dart` or `search_sort.dart` — Facet/Sort enum or model (typeIds: 43–44)
- `search_index_dto.dart` — SearchIndex DTO for API/transport
- `search_filter_dto.dart` — SearchFilter DTO for API/transport
- `search_result_dto.dart` — SearchResult DTO for API/transport
- `search_query_validator.dart` — Search query input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write flow orchestration
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** search (TaskSpec domain)
