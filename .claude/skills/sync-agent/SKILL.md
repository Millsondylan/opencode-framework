---
name: sync-agent
description: Offline sync — queue, conflict resolution, WorkManager/background_fetch
---

# sync-agent - Offline Sync

Configures offline sync — queue, conflict resolution, WorkManager/background_fetch. Produces sync infrastructure.

## Usage
```
/sync-agent
```

## Parameters
- None. This skill produces sync artifacts.

## What It Does
1. Implements **sync queue** — pending operations queue
2. Configures **conflict resolution** — last-write-wins, merge strategies
3. Integrates **WorkManager** (Android) / **background_fetch** (iOS)
4. Outputs **lib/core/sync/** — sync module
5. Outputs **sync queue service** — queue implementation
6. Outputs **conflict resolution** — resolution strategies

## Output
- `lib/core/sync/` — Sync module
- Sync queue service — pending operations queue
- Conflict resolution — resolution strategies

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository implementations (sync infrastructure only)

## Tech Stack
- **Sync:** Offline-first, queue-based
- **Background:** WorkManager, background_fetch
- **Conflict:** Last-write-wins, merge strategies
- **Platform:** Flutter/Dart (mobile)
