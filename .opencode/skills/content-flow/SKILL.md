---
name: content-flow
description: Implement content list, detail loading, and bookmark for the content domain
---

# content-flow - Content Domain Flow

Implements content list, detail loading, and bookmark. Third in the content domain chain (3/6).

## Usage
```
/content-flow
```

## Parameters
- None. This skill consumes content-schema and content-provider outputs and produces flow artifacts.

## What It Does
1. Implements **ContentNotifier** — Riverpod StateNotifier for content state
2. Defines **ContentState** — list, detail, bookmarks, loading, error
3. Registers **contentProvider**, **contentDetailProvider**, **bookmarkProvider**
4. Orchestrates **content list** — load, paginate, filter by category
5. Orchestrates **detail loading** — fetch by ID, cache
6. Orchestrates **bookmark** — add, remove, list
7. Handles **refresh** — pull-to-refresh, cache invalidation

## Output
- `content_notifier.dart` — ContentNotifier (StateNotifier<ContentState>)
- `content_state.dart` — ContentState sealed class / union type
- `content_provider.dart` — contentProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (content-schema responsibility)
- Write repository or data source code (content-provider responsibility)
- Write UI components or screens (content-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (content cache via provider)
- **Backend:** Supabase (via content-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** content (TaskSpec domain)
