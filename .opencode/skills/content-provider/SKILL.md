---
name: content-provider
description: Implement CMS integration and caching for the content domain
---

# content-provider - Content Domain Provider

Implements CMS integration and caching. Second in the content domain chain (2/6).

## Usage
```
/content-provider
```

## Parameters
- None. This skill consumes content-schema outputs and produces provider artifacts.

## What It Does
1. Implements **ContentRepository** — domain-facing repository interface
2. Implements **ContentRemoteDataSource** — Supabase or CMS API client
3. Implements **ContentLocalDataSource** — Hive cache for content
4. Handles **caching** — cache-first, stale-while-revalidate
5. Handles **categories** — list, filter, hierarchy
6. Supports **bookmarks** — save, list, remove

## Output
- `content_repository.dart` — ContentRepository implementation
- `content_remote_data_source.dart` — Supabase/CMS API client
- `content_local_data_source.dart` — Hive cache for content

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (content-schema responsibility)
- Write flow/state orchestration (content-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase or CMS API
- **Storage:** Hive (content cache)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** content (TaskSpec domain)
