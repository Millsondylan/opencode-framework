---
name: messaging-test
description: Write mock WebSocket and message flow tests for the messaging domain
---

# messaging-test - Messaging Domain Test

Writes mock WebSocket and message flow tests. Sixth in the messaging domain chain (6/6).

## Usage
```
/messaging-test
```

## Parameters
- None. This skill consumes all prior messaging domain outputs and produces test artifacts.

## What It Does
1. Writes **unit tests** for messaging logic (validators, guards, typing debounce)
2. Provides **mock WebSocket/Realtime** — fake connection for testing
3. Writes **message flow tests** — send, receive, persistence
4. Writes **conversation tests** — list, unread, sort
5. Achieves **>80% coverage** for messaging domain code
6. Uses `mocktail` or `mockito` for mocking; `flutter_test` for widget/integration tests

## Output
- `messaging_repository_test.dart` — Unit tests for MessagingRepository
- `messaging_notifier_test.dart` — Unit tests for MessagingNotifier
- `message_flow_test.dart` — Message flow tests
- `mock_realtime_client.dart` — Mock Supabase Realtime client for tests

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write implementation code (schema, provider, flow, guard, UI)
- Write production messaging logic
- Modify existing implementation files except to add testability hooks if strictly required

## Tech Stack
- **Testing:** flutter_test, mocktail or mockito
- **Backend Mock:** Mock Supabase Realtime client
- **State Mock:** Mock Riverpod overrides
- **Architecture:** Clean Architecture (test layer mirrors domain structure)
- **Domain:** messaging (TaskSpec domain)
