---
name: offline-sync-flow
description: Implement connectivity state, sync triggers, and retry logic for the offline-sync domain
---

# offline-sync-flow - Offline Sync Domain Flow

Implements connectivity state, sync triggers, and retry logic for offline-sync. Third in the offline-sync domain chain (3/6).

## Usage
```
/offline-sync-flow
```

## Parameters
- None. This skill consumes offline-sync-schema and offline-sync-provider outputs and produces flow artifacts.

## What It Does
1. Implements **SyncNotifier** — Riverpod StateNotifier for sync state
2. Defines **SyncState** — idle, syncing, conflicted, offline, error
3. Registers **syncProvider** — Riverpod provider exposing SyncNotifier
4. Monitors **connectivity** — network status, online/offline transitions
5. Implements **sync triggers** — app resume, connectivity change, manual trigger
6. Implements **retry logic** — exponential backoff, max retries
7. Handles **conflict resolution flow** — detect, present, resolve

## Output
- `sync_notifier.dart` — SyncNotifier (StateNotifier<SyncState>)
- `sync_state.dart` — SyncState sealed class / union type
- `sync_provider.dart` — syncProvider (Riverpod Provider)
- Connectivity monitoring integration

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (offline-sync-schema responsibility)
- Write repository or data source code (offline-sync-provider responsibility)
- Write UI components or screens (offline-sync-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (queue persistence via provider)
- **Backend:** Supabase (via offline-sync-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** offline-sync (TaskSpec domain)
