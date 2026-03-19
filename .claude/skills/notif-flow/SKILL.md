---
name: notif-flow
description: Implement permission flow, notification routing, and deep link handling with Riverpod
---

# notif-flow - Notifications Domain Flow

Implements permission flow orchestration, notification routing, and deep link handling with Riverpod. Third in the notifications domain chain (3/6).

## Usage
```
/notif-flow
```

## Parameters
- None. This skill consumes notif-schema and notif-provider outputs and produces flow artifacts.

## What It Does
1. Implements **NotificationNotifier** — Riverpod StateNotifier for notification state
2. Defines **permission state** — granted, denied, permanently-denied, undetermined, loading
3. Orchestrates **permission flow** — request → platform check → state update
4. Implements **notification routing** — route incoming notifications to correct handlers/screens
5. Implements **deep link handling** — parse notification payloads, navigate to target screen
6. Registers **notifProvider** — Riverpod provider exposing NotificationNotifier
7. Handles **notification lifecycle** — received, opened, dismissed, foreground/background
8. Coordinates with **notif-provider** — permission check, token registration, routing config

## Output
- `notification_notifier.dart` — NotificationNotifier (StateNotifier<NotificationState>)
- `notification_state.dart` — NotificationState with permission state variants
- `notif_provider.dart` — notifProvider (Riverpod Provider)
- `notification_router.dart` — routing logic for incoming notifications
- `deep_link_handler.dart` — deep link parsing and navigation dispatch

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (notif-schema responsibility)
- Write repository or data source code (notif-provider responsibility)
- Write UI components or screens (notif-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (permission state cache, routing config, if needed)
- **Backend:** Supabase (via notif-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** notif (TaskSpec domain)
