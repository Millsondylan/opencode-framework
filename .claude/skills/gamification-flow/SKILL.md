---
name: gamification-flow
description: Implement points balance, badge unlocks, and streak for the gamification domain
---

# gamification-flow - Gamification Domain Flow

Implements points balance, badge unlocks, and streak. Third in the gamification domain chain (3/6).

## Usage
```
/gamification-flow
```

## Parameters
- None. This skill consumes gamification-schema and gamification-provider outputs and produces flow artifacts.

## What It Does
1. Implements **GamificationNotifier** — Riverpod StateNotifier for gamification state
2. Defines **GamificationState** — points, badges, leaderboard, streak, loading, error
3. Registers **gamificationProvider**, **pointsProvider**, **badgeProvider**
4. Orchestrates **points balance** — add, deduct, refresh
5. Orchestrates **badge unlocks** — check criteria, award, notify
6. Orchestrates **streak** — daily check-in, streak count, reset
7. Handles **leaderboard** — fetch, rank, refresh

## Output
- `gamification_notifier.dart` — GamificationNotifier (StateNotifier<GamificationState>)
- `gamification_state.dart` — GamificationState sealed class / union type
- `gamification_provider.dart` — gamificationProvider (Riverpod Provider)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (gamification-schema responsibility)
- Write repository or data source code (gamification-provider responsibility)
- Write UI components or screens (gamification-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (cache via provider)
- **Backend:** Supabase (via gamification-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** gamification (TaskSpec domain)
