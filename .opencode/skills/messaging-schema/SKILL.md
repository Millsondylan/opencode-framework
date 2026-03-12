---
name: messaging-schema
description: Define conversation, message, typing, and type IDs 100–109 for the messaging domain
---

# messaging-schema - Messaging Domain Schema

Defines conversation, message, typing indicator, and messaging state types for the messaging domain. First in the messaging domain chain (1/6).

## Usage
```
/messaging-schema
```

## Parameters
- None. This skill produces schema artifacts for the messaging domain.

## What It Does
1. Defines **Conversation** entity with Hive persistence (`@HiveType` typeId: 100)
2. Defines **Message** model with Hive persistence (typeId: 101)
3. Defines **TypingIndicator** model with Hive persistence (typeId: 102)
4. Creates **ConversationDTO**, **MessageDTO** for API/transport layer
5. Creates **MessageValidator** for input validation
6. Defines message types (text, image, system, delivery status)

## Output
- `conversation.dart` — Conversation model with `@HiveType(typeId: 100)`
- `message.dart` — Message model with `@HiveType(typeId: 101)`
- `typing_indicator.dart` — TypingIndicator model with `@HiveType(typeId: 102)`
- `conversation_dto.dart` — Conversation DTO for API/transport
- `message_dto.dart` — Message DTO for API/transport
- `message_validator.dart` — Message input validation

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository code
- Write state management (Riverpod providers)
- Write UI components
- Write tests

## Tech Stack
- **Persistence:** Hive (local storage)
- **Architecture:** Clean Architecture (domain/entity layer)
- **Domain:** messaging (TaskSpec domain)
