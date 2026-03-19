---
name: notif-provider
description: Implement FCM/APNs setup, local notifications, topic subscription, and NotificationRepository for the notifications domain
---

# notif-provider - Notifications Domain Provider

Implements FCM/APNs integration, local notifications, topic subscription, and the notification repository layer. Second in the notifications domain chain (2/6).

## Usage
```
/notif-provider
```

## Parameters
- None. This skill consumes notif-schema outputs and produces provider artifacts.

## What It Does
1. Integrates **Firebase Cloud Messaging (FCM)** — push token registration, message handling
2. Integrates **Apple Push Notification service (APNs)** — iOS push setup, token handling
3. Implements **local notifications** — scheduling, display, platform channels (flutter_local_notifications)
4. Implements **topic subscription** — subscribe/unsubscribe to FCM topics
5. Implements **NotificationRepository** — domain-facing repository interface
6. Implements **NotificationRemoteDataSource** — FCM/APNs client wrapper
7. Handles push token persistence and refresh

## Output
- `notification_repository.dart` — NotificationRepository implementation
- `notification_remote_data_source.dart` — FCM/APNs client wrapper
- `fcm_service.dart` — FCM integration (token, messaging)
- `apns_service.dart` — APNs integration (iOS push)
- `local_notification_service.dart` — Local notification scheduling and display

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (notif-schema responsibility)
- Write flow/state orchestration (notif-flow responsibility)
- Write UI components
- Write tests

## Tech Stack
- **Backend:** Firebase Cloud Messaging (FCM), APNs
- **Local:** flutter_local_notifications
- **State:** Riverpod (provider registration only, not flow logic)
- **Storage:** Hive (push token, preferences)
- **Architecture:** Clean Architecture (data layer)
- **Domain:** notifications (TaskSpec domain)
