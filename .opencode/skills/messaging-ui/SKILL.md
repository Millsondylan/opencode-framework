---
name: messaging-ui
description: Implement ChatScreen, message bubbles, and typing indicator for the messaging domain
---

# messaging-ui - Messaging Domain UI

Implements ChatScreen, message bubbles, and typing indicator. Fourth in the messaging domain chain (4/6).

## Usage
```
/messaging-ui
```

## Parameters
- None. This skill consumes messaging-flow outputs and produces UI artifacts.

## What It Does
1. Implements **ChatScreen** — conversation view, message list, input
2. Implements **MessageBubble** — sent/received styling, timestamps, status
3. Implements **TypingIndicator** — animated dots or text
4. Implements **ConversationListScreen** — conversation list, preview, unread badge
5. Handles **input** — text field, send button, attachments
6. Uses **Material 3** — components, theming, typography

## Output
- `chat_screen.dart` — ChatScreen widget
- `message_bubble.dart` — MessageBubble widget
- `typing_indicator_widget.dart` — TypingIndicator widget
- `conversation_list_screen.dart` — ConversationListScreen widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (messaging-schema responsibility)
- Write repository or data source code (messaging-provider responsibility)
- Write flow/state orchestration (messaging-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read messagingProvider, call MessagingNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** messaging (TaskSpec domain)
