---
name: social-test
description: Write feed pagination and follow state tests for the social domain
---

# social-test - Social Domain Test

Writes feed pagination and follow state tests. Sixth in the social domain chain (6/6).

## Usage
```
/social-test
```

## Parameters
- None. This skill consumes all prior social domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for social logic (profile, follow, feed, guards)
2. Writes **feed pagination tests** — load more, refresh, cursor
3. Writes **follow state tests** — follow, unfollow, follower count
4. Provides **mock social repository** for isolated testing
5. Achieves **>80% coverage** for social domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `profile_repository_test.dart` — Unit tests for ProfileRepository
- `feed_repository_test.dart` — Unit tests for FeedRepository
- `social_notifier_test.dart` — Unit tests for SocialNotifier
- `feed_pagination_test.dart` — Feed pagination tests
- `mock_social_repository.dart` — Mock social repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production social logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** social (TaskSpec domain)
