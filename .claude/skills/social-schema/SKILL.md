---
name: social-schema
description: Define profile, follow, feed, and type IDs 90–99 for the social domain
---

# social-schema - Social Domain Schema

Defines profile, follow, feed, and social state types for the social domain. First in the social domain chain (1/6).

## Usage
```
/social-schema
```

## Parameters
- None. This skill produces schema artifacts for the social domain.

## What It Does
1. Defines **Profile** entity with Hive persistence (`@HiveType` typeId: 90)
2. Defines **Follow** model with Hive persistence (typeId: 91)
3. Defines **FeedItem** model with Hive persistence (typeId: 92)
4. Creates **ProfileDTO**, **FollowDTO**, **FeedItemDTO** for API/transport layer
5. Creates **ProfileValidator** for input validation
6. Defines feed item types (post, repost, reaction)

## Output
- `profile.dart` — Profile model with `@HiveType(typeId: 90)`
- `follow.dart` — Follow model with `@HiveType(typeId: 91)`
- `feed_item.dart` — FeedItem model with `@HiveType(typeId: 92)`
- `profile_dto.dart` — Profile DTO for API/transport
- `follow_dto.dart` — Follow DTO for API/transport
- `profile_validator.dart` — Profile input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** social (TaskSpec domain)
