---
name: offline-sync-guard
description: Implement data integrity checks and conflict policies for the offline-sync domain
---

# offline-sync-guard - Offline Sync Domain Guard

Implements data integrity checks and conflict policies. Fifth in the offline-sync domain chain (5/6).

## Usage
```
/offline-sync-guard
```

## Parameters
- None. This skill consumes offline-sync-schema and offline-sync-provider outputs and produces guard artifacts.

## What It Does
1. Implements **SyncIntegrityGuard** — validates queue items before sync
2. Implements **ConflictPolicy** — last-write-wins, server-wins, merge strategies
3. Implements **SyncValidationGuard** — checks data consistency before enqueue
4. Integrates with Riverpod sync state for guard decisions
5. Handles **orphan detection** — references to deleted entities

## Output
- `sync_integrity_guard.dart` — SyncIntegrityGuard for validation
- `conflict_policy.dart` — ConflictPolicy implementation
- `sync_validation_guard.dart` — SyncValidationGuard for pre-sync checks

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (offline-sync-schema responsibility)
- Write provider/repository code (offline-sync-provider responsibility)
- Write flow/state orchestration (offline-sync-flow responsibility)
- Write UI components or screens
- Write tests (offline-sync-test responsibility)

## Tech Stack
- **State:** Riverpod (reads sync state for guard decisions)
- **Storage:** Hive (queue persistence)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** offline-sync (TaskSpec domain)
