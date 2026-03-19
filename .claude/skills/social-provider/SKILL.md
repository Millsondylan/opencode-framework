---
name: social-provider
description: Implement profile CRUD, follow API, and feed aggregation for the social domain
---

# social-provider - Social Domain Provider

Implements profile CRUD, follow API, and feed aggregation. Second in the social domain chain (2/6).

## Usage
```
/social-provider
```

## Parameters
- None. This skill consumes social-schema outputs and produces provider artifacts.

## What It Does
1. Implements **ProfileRepository** — domain-facing repository interface
2. Implements **FollowRepository** — follow/unfollow, follower/following lists
3. Implements **FeedRepository** — feed aggregation, pagination
4. Implements **SocialRemoteDataSource** — Supabase client for profiles, follows, feed
5. Implements **SocialLocalDataSource** — Hive cache for profiles, feed
6. Handles **reactions** — like, repost, comment counts

## Output
- `profile_repository.dart` — ProfileRepository implementation
- `follow_repository.dart` — FollowRepository implementation
- `feed_repository.dart` — FeedRepository implementation
- `social_remote_data_source.dart` — Supabase client wrapper
- `social_local_data_source.dart` — Hive cache

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (social-schema responsibility)
- Write flow/state orchestration (social-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase
- **Storage:** Hive (cache)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** social (TaskSpec domain)
