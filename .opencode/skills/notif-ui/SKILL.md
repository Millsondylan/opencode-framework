---
name: notif-ui
description: Implement notification preferences screen and in-app notification center with Material 3
---

# notif-ui - Notifications Domain UI

Implements notification preferences screen and in-app notification center with Material 3. Fourth in the notifications domain chain (4/6).

## Usage
```
/notif-ui
```

## Parameters
- None. This skill consumes notif-flow outputs and produces UI artifacts.

## What It Does
1. Implements **NotificationPreferencesScreen** — toggle switches for notification types, permission status, settings
2. Implements **notification center UI** — in-app list of notifications, read/unread, swipe actions
3. Adds **permission prompt UI** — rationale, request CTA, link to app settings when denied
4. Handles **notification list states** — empty, loading, error, success
5. Adds **notification item cards** — title, body, timestamp, icon, tap to open/deep link
6. Handles **error states** — snackbars, banners, inline error messages for permission failures
7. Uses **Material 3** — components, theming, typography

## Output
- `notification_preferences_screen.dart` — NotificationPreferencesScreen widget
- `notification_center_screen.dart` — In-app notification center widget
- `notification_item_tile.dart` — Notification item card/tile component
- Permission prompt UI components (rationale, request button, settings link)
- Notification list UI components (empty state, loading, error)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (notif-schema responsibility)
- Write repository or data source code (notif-provider responsibility)
- Write flow/state orchestration (notif-flow responsibility)
- Write route guards or notification middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read notifProvider, call NotificationNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** notif (TaskSpec domain)
