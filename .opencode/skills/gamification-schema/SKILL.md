---
name: gamification-schema
description: Define points, badge, leaderboard, and type IDs 160–169 for the gamification domain
---

# gamification-schema - Gamification Domain Schema

Defines points, badge, leaderboard, and gamification state types for the gamification domain. First in the gamification domain chain (1/6).

## Usage
```
/gamification-schema
```

## Parameters
- None. This skill produces schema artifacts for the gamification domain.

## What It Does
1. Defines **Points** entity with Hive persistence (`@HiveType` typeId: 160)
2. Defines **Badge** model with Hive persistence (typeId: 161)
3. Defines **LeaderboardEntry** model with Hive persistence (typeId: 162)
4. Creates **PointsDTO**, **BadgeDTO**, **LeaderboardEntryDTO** for API/transport layer
5. Creates **PointsValidator** for input validation
6. Defines badge types (achievement, milestone, special)

## Output
- `points.dart` — Points model with `@HiveType(typeId: 160)`
- `badge.dart` — Badge model with `@HiveType(typeId: 161)`
- `leaderboard_entry.dart` — LeaderboardEntry model with `@HiveType(typeId: 162)`
- `points_dto.dart` — Points DTO for API/transport
- `badge_dto.dart` — Badge DTO for API/transport
- `points_validator.dart` — Points input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** gamification (TaskSpec domain)
