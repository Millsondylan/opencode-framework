---
name: gamification-provider
description: Implement points service, badge awards, and leaderboard for the gamification domain
---

# gamification-provider - Gamification Domain Provider

Implements points service, badge awards, and leaderboard. Second in the gamification domain chain (2/6).

## Usage
```
/gamification-provider
```

## Parameters
- None. This skill consumes gamification-schema outputs and produces provider artifacts.

## What It Does
1. Implements **PointsRepository** — add points, get balance, transaction history
2. Implements **BadgeRepository** — list badges, award, check criteria
3. Implements **LeaderboardRepository** — fetch rankings, user position
4. Implements **GamificationRemoteDataSource** — Supabase client
5. Implements **GamificationLocalDataSource** — Hive cache for points, badges
6. Handles **streak tracking** — daily streak, reset logic

## Output
- `points_repository.dart` — PointsRepository implementation
- `badge_repository.dart` — BadgeRepository implementation
- `leaderboard_repository.dart` — LeaderboardRepository implementation
- `gamification_remote_data_source.dart` — Supabase client
- `gamification_local_data_source.dart` — Hive cache

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (gamification-schema responsibility)
- Write flow/state orchestration (gamification-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase
- **Storage:** Hive (cache)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** gamification (TaskSpec domain)
