---
name: gamification-guard
description: Implement anti-cheat and integrity checks for the gamification domain
---

# gamification-guard - Gamification Domain Guard

Implements anti-cheat and integrity checks. Fifth in the gamification domain chain (5/6).

## Usage
```
/gamification-guard
```

## Parameters
- None. This skill consumes gamification-schema and gamification-provider outputs and produces guard artifacts.

## What It Does
1. Implements **AntiCheatGuard** — detect impossible point gains, rate limits
2. Implements **IntegrityGuard** — validate points/badge consistency server-side
3. Integrates with Riverpod gamification state for guard decisions
4. Handles **suspicious activity** — flag, throttle, block
5. Handles **server validation** — all point/badge changes verified server-side

## Output
- `anti_cheat_guard.dart` — AntiCheatGuard
- `integrity_guard.dart` — IntegrityGuard

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (gamification-schema responsibility)
- Write provider/repository code (gamification-provider responsibility)
- Write flow/state orchestration (gamification-flow responsibility)
- Write UI components or screens
- Write tests (gamification-test responsibility)

## Tech Stack
- **State:** Riverpod (reads gamification state for guard decisions)
- **Backend:** Supabase (validation API)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** gamification (TaskSpec domain)
