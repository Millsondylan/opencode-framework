---
name: gamification-ui
description: Implement PointsDisplay, BadgeCollectionScreen, and leaderboard for the gamification domain
---

# gamification-ui - Gamification Domain UI

Implements PointsDisplay, BadgeCollectionScreen, and leaderboard. Fourth in the gamification domain chain (4/6).

## Usage
```
/gamification-ui
```

## Parameters
- None. This skill consumes gamification-flow outputs and produces UI artifacts.

## What It Does
1. Implements **PointsDisplay** — points balance, animation on change
2. Implements **BadgeCollectionScreen** — badge grid, locked/unlocked, progress
3. Implements **LeaderboardScreen** — rankings, user highlight, period filter
4. Implements **StreakDisplay** — streak count, flame icon, reset message
5. Implements **BadgeUnlockOverlay** — celebration on new badge
6. Uses **Material 3** — components, theming, typography

## Output
- `points_display.dart` — PointsDisplay widget
- `badge_collection_screen.dart` — BadgeCollectionScreen widget
- `leaderboard_screen.dart` — LeaderboardScreen widget
- `streak_display.dart` — StreakDisplay widget
- `badge_unlock_overlay.dart` — BadgeUnlockOverlay widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (gamification-schema responsibility)
- Write repository or data source code (gamification-provider responsibility)
- Write flow/state orchestration (gamification-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read gamificationProvider, call GamificationNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** gamification (TaskSpec domain)
