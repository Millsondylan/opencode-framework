---
name: messaging-flow
description: Implement conversation list, message flow, and typing debounce for the messaging domain
---

# messaging-flow - Messaging Domain Flow

Implements conversation list, message flow, and typing debounce. Third in the messaging domain chain (3/6).

## Usage
```
/messaging-flow
```

## Parameters
- None. This skill consumes messaging-schema and messaging-provider outputs and produces flow artifacts.

## What It Does
1. Implements **MessagingNotifier** — Riverpod StateNotifier for messaging state
2. Defines **MessagingState** — conversations, messages, typing, loading, error
3. Registers **messagingProvider**, **conversationProvider**, **messageProvider**
4. Orchestrates **conversation list** — load, sort, unread count
5. Orchestrates **message flow** — send, receive, realtime updates
6. Implements **typing debounce** — throttle typing events, timeout
7. Handles **message delivery** — sent, delivered, read status

## Output
- `messaging_notifier.dart` — MessagingNotifier (StateNotifier<MessagingState>)
- `messaging_state.dart` — MessagingState sealed class / union type
- `messaging_provider.dart` — messagingProvider (Riverpod Provider)
- Typing debounce utilities

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (messaging-schema responsibility)
- Write repository or data source code (messaging-provider responsibility)
- Write UI components or screens (messaging-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (message persistence via provider)
- **Backend:** Supabase Realtime (via messaging-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** messaging (TaskSpec domain)
