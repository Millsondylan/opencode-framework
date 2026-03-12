---
name: social-ui
description: Implement ProfileScreen, FollowersScreen, and feed cards for the social domain
---

# social-ui - Social Domain UI

Implements ProfileScreen, FollowersScreen, and feed cards. Fourth in the social domain chain (4/6).

## Usage
```
/social-ui
```

## Parameters
- None. This skill consumes social-flow outputs and produces UI artifacts.

## What It Does
1. Implements **ProfileScreen** — avatar, bio, follow button, stats
2. Implements **FollowersScreen** — follower/following list, search
3. Implements **FeedCard** — post content, author, reactions, actions
4. Implements **FeedScreen** — feed list, pull-to-refresh, infinite scroll
5. Handles **loading and error states** — skeletons, empty states
6. Uses **Material 3** — components, theming, typography

## Output
- `profile_screen.dart` — ProfileScreen widget
- `followers_screen.dart` — FollowersScreen widget
- `feed_card.dart` — FeedCard widget
- `feed_screen.dart` — FeedScreen widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (social-schema responsibility)
- Write repository or data source code (social-provider responsibility)
- Write flow/state orchestration (social-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read socialProvider, feedProvider, call SocialNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** social (TaskSpec domain)
