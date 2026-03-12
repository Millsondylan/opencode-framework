---
name: offline-sync-provider
description: Implement queue persistence, batch sync, and delta detection for the offline-sync domain
---

# offline-sync-provider - Offline Sync Domain Provider

Implements sync queue persistence, batch sync, and delta detection. Second in the offline-sync domain chain (2/6).

## Usage
```
/offline-sync-provider
```

## Parameters
- None. This skill consumes offline-sync-schema outputs and produces provider artifacts.

## What It Does
1. Implements **SyncQueueRepository** — domain-facing repository interface
2. Implements **SyncQueueLocalDataSource** — Hive persistence for queue items
3. Implements **SyncRemoteDataSource** — Supabase/API client for batch sync
4. Implements **queue persistence** — enqueue, dequeue, retry logic
5. Implements **batch sync** — grouped uploads, conflict detection
6. Implements **delta detection** — change tracking, last-sync timestamp

## Output
- `sync_queue_repository.dart` — SyncQueueRepository implementation
- `sync_queue_local_data_source.dart` — SyncQueueLocalDataSource (Hive)
- `sync_remote_data_source.dart` — SyncRemoteDataSource (Supabase/API)
- Batch sync and delta detection utilities

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (offline-sync-schema responsibility)
- Write flow/state orchestration (offline-sync-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase
- **Storage:** Hive (queue persistence)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** offline-sync (TaskSpec domain)
