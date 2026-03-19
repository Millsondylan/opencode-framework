---
name: messaging-provider
description: Implement WebSocket/Realtime and message persistence for the messaging domain
---

# messaging-provider - Messaging Domain Provider

Implements WebSocket/Realtime integration and message persistence. Second in the messaging domain chain (2/6).

## Usage
```
/messaging-provider
```

## Parameters
- None. This skill consumes messaging-schema outputs and produces provider artifacts.

## What It Does
1. Integrates **Supabase Realtime** or **WebSocket** for live messaging
2. Implements **MessagingRepository** — domain-facing repository interface
3. Implements **MessagingRemoteDataSource** — Realtime/WebSocket client
4. Implements **MessagingLocalDataSource** — Hive persistence for messages
5. Handles **message persistence** — offline queue, sync on reconnect
6. Handles **typing events** — subscribe, broadcast, debounce

## Output
- `messaging_repository.dart` — MessagingRepository implementation
- `messaging_remote_data_source.dart` — Supabase Realtime/WebSocket client
- `messaging_local_data_source.dart` — Hive persistence for messages

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (messaging-schema responsibility)
- Write flow/state orchestration (messaging-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Supabase Realtime
- **Storage:** Hive (message persistence)
- **State:** Riverpod (provider registration only, not flow logic)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** messaging (TaskSpec domain)
