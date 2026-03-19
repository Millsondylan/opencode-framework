---
name: local-storage-agent
description: Hive/Isar/SharedPreferences/SQLite
---

# local-storage-agent - Local Storage

Configures Hive, Isar, SharedPreferences, or SQLite for local persistence. Produces storage infrastructure and type adapter registration.

## Usage
```
/local-storage-agent
```

## Parameters
- None. This skill produces local storage artifacts.

## What It Does
1. Configures **Hive** (or Isar/SharedPreferences/SQLite)
2. Implements **Hive init** — initialization, path setup
3. Registers **type adapters** — HiveType adapters for models
4. Outputs **lib/core/storage/** — storage module
5. Outputs **Hive init** — initialization code
6. Outputs **type adapter registration** — adapter registration

## Output
- `lib/core/storage/` — Storage module
- Hive init — initialization and path setup
- Type adapter registration — HiveType adapter registration

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository implementations (storage only)

## Tech Stack
- **Storage:** Hive, Isar, SharedPreferences, SQLite
- **Architecture:** Clean Architecture (data layer)
- **Platform:** Flutter/Dart (mobile)
