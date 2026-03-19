---
name: social-flow
description: Implement profile state, feed pagination, and reactions for the social domain
---

# social-flow - Social Domain Flow

Implements profile state, feed pagination, and reactions. Third in the social domain chain (3/6).

## Usage
```
/social-flow
```

## Parameters
- None. This skill consumes social-schema and social-provider outputs and produces flow artifacts.

## What It Does
1. Implements **SocialNotifier** — Riverpod StateNotifier for social state
2. Defines **SocialState** — profile, feed, follow status, loading, error
3. Registers **socialProvider**, **feedProvider**, **profileProvider**
4. Orchestrates **profile state** — load, update, cache
5. Orchestrates **feed pagination** — load more, refresh, infinite scroll
6. Orchestrates **reactions** — like, repost, comment
7. Handles **follow state** — follow, unfollow, follower count

## Output
- `social_notifier.dart` — SocialNotifier (StateNotifier<SocialState>)
- `social_state.dart` — SocialState sealed class / union type
- `social_provider.dart` — socialProvider (Riverpod Provider)
- `feed_provider.dart` — feedProvider for feed pagination

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (social-schema responsibility)
- Write repository or data source code (social-provider responsibility)
- Write UI components or screens (social-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (cache via provider)
- **Backend:** Supabase (via social-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** social (TaskSpec domain)
