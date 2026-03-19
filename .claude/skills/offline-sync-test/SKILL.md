---
name: offline-sync-test
description: Write offline simulation, conflict tests, and mock sync for the offline-sync domain
---

# offline-sync-test - Offline Sync Domain Test

Writes offline simulation, conflict tests, and mock sync. Sixth in the offline-sync domain chain (6/6).

## Usage
```
/offline-sync-test
```

## Parameters
- None. This skill consumes all prior offline-sync domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for sync logic (queue, delta detection, conflict resolution)
2. Writes **offline simulation tests** — mock connectivity, queue persistence
3. Writes **conflict tests** — conflict detection, resolution policies
4. Provides **mock sync repository** for isolated testing
5. Achieves **>80% coverage** for offline-sync domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `sync_queue_repository_test.dart` — Unit tests for SyncQueueRepository
- `sync_notifier_test.dart` — Unit tests for SyncNotifier
- `conflict_resolution_test.dart` — Conflict resolution tests
- `offline_simulation_test.dart` — Offline simulation tests
- `mock_sync_repository.dart` — Mock sync repository for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production sync logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** offline-sync (TaskSpec domain)
