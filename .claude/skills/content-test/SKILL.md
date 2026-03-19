---
name: content-test
description: Write pagination and rich text tests for the content domain
---

# content-test - Content Domain Test

Writes pagination and rich text tests. Sixth in the content domain chain (6/6).

## Usage
```
/content-test
```

## Parameters
- None. This skill consumes all prior content domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for content logic (validators, guards, access control)
2. Writes **pagination tests** — load more, refresh, cursor
3. Writes **rich text tests** — rendering, sanitization
4. Provides **mock content repository** for isolated testing
5. Achieves **>80% coverage** for content domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `content_repository_test.dart` — Unit tests for ContentRepository
- `content_notifier_test.dart` — Unit tests for ContentNotifier
- `pagination_test.dart` — Pagination tests
- `rich_text_test.dart` — Rich text tests
- `mock_content_repository.dart` — Mock content repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production content logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** content (TaskSpec domain)
