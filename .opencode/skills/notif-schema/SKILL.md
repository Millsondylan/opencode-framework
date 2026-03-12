---
name: notif-schema
description: Define notification models, channel definitions, and preference schema for the notifications domain
---

# notif-schema - Notifications Domain Schema

Defines notification entities, channel definitions, preference schema, and DTOs for the notifications domain. First in the notifications domain chain (1/6).

## Usage
```
/notif-schema
```

## Parameters
- None. This skill produces schema artifacts for the notifications domain.

## What It Does
1. Defines **Notification** entity with Hive persistence (`@HiveType` typeId: 30)
2. Defines **NotificationChannel** enum (push, email, in-app, SMS) with Hive persistence (typeId: 31)
3. Defines **NotificationPreference** model with Hive persistence (typeId: 32)
4. Creates **NotificationDTO** and **NotificationPreferenceDTO** for API/transport layer
5. Creates **NotificationValidator** for input validation
6. Defines notification state types (unread, read, dismissed, archived)

## Output
- `notification_entity.dart` — Notification model with `@HiveType(typeId: 30)`
- `notification_channel.dart` — Channel enum with `@HiveType(typeId: 31)`
- `notification_preference.dart` — Preference model with `@HiveType(typeId: 32)`
- `notification_dto.dart` — Notification DTO for API/transport
- `notification_preference_dto.dart` — Preference DTO for API/transport
- `notification_validator.dart` — Notification input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write flow logic
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** notifications (TaskSpec domain)
