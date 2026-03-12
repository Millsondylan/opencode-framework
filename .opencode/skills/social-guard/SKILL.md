---
name: social-guard
description: Implement block/mute and content reporting for the social domain
---

# social-guard - Social Domain Guard

Implements block/mute and content reporting. Fifth in the social domain chain (5/6).

## Usage
```
/social-guard
```

## Parameters
- None. This skill consumes social-schema and social-provider outputs and produces guard artifacts.

## What It Does
1. Implements **BlockGuard** — block user, hide blocked content
2. Implements **MuteGuard** — mute user, hide muted content
3. Implements **ContentReportGuard** — report post, user, abuse flow
4. Integrates with Riverpod social state for guard decisions
5. Handles **blocked/muted list** — persistence, sync

## Output
- `block_guard.dart` — BlockGuard for user blocking
- `mute_guard.dart` — MuteGuard for user muting
- `content_report_guard.dart` — ContentReportGuard for reporting

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (social-schema responsibility)
- Write provider/repository code (social-provider responsibility)
- Write flow/state orchestration (social-flow responsibility)
- Write UI components or screens
- Write tests (social-test responsibility)

## Tech Stack
- **State:** Riverpod (reads social state for guard decisions)
- **Storage:** Hive (block/mute list)
- **Backend:** Supabase (report API)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** social (TaskSpec domain)
