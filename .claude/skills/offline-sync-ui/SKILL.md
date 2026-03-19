---
name: offline-sync-ui
description: Implement sync status display and conflict resolution UI for the offline-sync domain
---

# offline-sync-ui - Offline Sync Domain UI

Implements sync status display and conflict resolution UI. Fourth in the offline-sync domain chain (4/6).

## Usage
```
/offline-sync-ui
```

## Parameters
- None. This skill consumes offline-sync-flow outputs and produces UI artifacts.

## What It Does
1. Implements **SyncStatusBanner** — shows sync state (syncing, offline, error)
2. Implements **ConflictResolutionScreen** — presents conflicts, accept/resolve actions
3. Implements **SyncIndicator** — small status icon in app bar or nav
4. Handles **error states** — snackbars, banners for sync failures
5. Uses **Material 3** — components, theming, typography

## Output
- `sync_status_banner.dart` — SyncStatusBanner widget
- `conflict_resolution_screen.dart` — ConflictResolutionScreen widget
- `sync_indicator.dart` — SyncIndicator widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (offline-sync-schema responsibility)
- Write repository or data source code (offline-sync-provider responsibility)
- Write flow/state orchestration (offline-sync-flow responsibility)
- Write route guards or sync middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read syncProvider, call SyncNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** offline-sync (TaskSpec domain)
