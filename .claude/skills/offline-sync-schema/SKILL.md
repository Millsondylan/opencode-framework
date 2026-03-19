---
name: offline-sync-schema
description: Define sync queue, conflict resolution, and type IDs 60–69 for the offline-sync domain
---

# offline-sync-schema - Offline Sync Domain Schema

Defines the sync queue model, conflict resolution types, and sync state types for the offline-sync domain. First in the offline-sync domain chain (1/6).

## Usage
```
/offline-sync-schema
```

## Parameters
- None. This skill produces schema artifacts for the offline-sync domain.

## What It Does
1. Defines **SyncQueueItem** entity with Hive persistence (`@HiveType` typeId: 60)
2. Defines **ConflictResolution** model with Hive persistence (typeId: 61)
3. Defines **SyncStatus** enum with Hive persistence (typeId: 62)
4. Creates **SyncQueueItemDTO** and **ConflictResolutionDTO** for API/transport layer
5. Creates **SyncQueueValidator** for input validation
6. Defines sync state types (pending, syncing, conflicted, resolved, failed)

## Output
- `sync_queue_item.dart` — SyncQueueItem model with `@HiveType(typeId: 60)`
- `conflict_resolution.dart` — ConflictResolution model with `@HiveType(typeId: 61)`
- `sync_status.dart` — SyncStatus enum with `@HiveType(typeId: 62)`
- `sync_queue_item_dto.dart` — SyncQueueItem DTO for API/transport
- `conflict_resolution_dto.dart` — ConflictResolution DTO for API/transport
- `sync_queue_validator.dart` — SyncQueue input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** offline-sync (TaskSpec domain)
