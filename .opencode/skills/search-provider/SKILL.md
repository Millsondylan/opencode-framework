---
name: search-provider
description: Implement Algolia, Meilisearch, or local search integration with repository and datasources for the search domain
---

# search-provider - Search Domain Provider

Implements Algolia, Meilisearch, or local search integration, repository layer, remote/local data sources, and search client wrappers. Second in the search domain chain (2/6).

## Usage
```
/search-provider
```

## Parameters
- None. This skill consumes search-schema outputs and produces provider artifacts.

## What It Does
1. Integrates **Algolia** and/or **Meilisearch** and/or **local search** (query, facets, filters, sort)
2. Implements **SearchRepository** — domain-facing repository interface
3. Implements **SearchRemoteDataSource** — Algolia/Meilisearch client wrapper
4. Implements **SearchLocalDataSource** — Hive or local cache for offline search index
5. Handles search queries, facet aggregation, and result pagination
6. Supports index sync and incremental updates for local search

## Output
- `search_repository.dart` — SearchRepository implementation
- `search_remote_data_source.dart` — SearchRemoteDataSource (Algolia/Meilisearch)
- `search_local_data_source.dart` — SearchLocalDataSource (Hive/local cache)
- Search integration adapters for chosen provider(s)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (search-schema responsibility)
- Write flow/state orchestration (search-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Algolia, Meilisearch, or local search (one or more)
- **State:** Riverpod (provider registration only, not flow logic)
- **Storage:** Hive for local search index cache
- **Architecture:** Clean Architecture (data layer)
- **Domain:** search (TaskSpec domain)
