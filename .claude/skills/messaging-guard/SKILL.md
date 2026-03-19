---
name: messaging-guard
description: Implement content validation, rate limit, and spam detection for the messaging domain
---

# messaging-guard - Messaging Domain Guard

Implements content validation, rate limit, and spam detection. Fifth in the messaging domain chain (5/6).

## Usage
```
/messaging-guard
```

## Parameters
- None. This skill consumes messaging-schema and messaging-provider outputs and produces guard artifacts.

## What It Does
1. Implements **ContentValidationGuard** — profanity, length, format validation
2. Implements **RateLimitGuard** — message send rate, throttle
3. Implements **SpamGuard** — duplicate detection, spam patterns
4. Integrates with Riverpod messaging state for guard decisions
5. Handles **rejection** — user feedback when guard fails

## Output
- `content_validation_guard.dart` — ContentValidationGuard
- `rate_limit_guard.dart` — RateLimitGuard
- `spam_guard.dart` — SpamGuard

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (messaging-schema responsibility)
- Write provider/repository code (messaging-provider responsibility)
- Write flow/state orchestration (messaging-flow responsibility)
- Write UI components or screens
- Write tests (messaging-test responsibility)

## Tech Stack
- **State:** Riverpod (reads messaging state for guard decisions)
- **Architecture:** Clean Architecture (guard layer)
- **Domain:** messaging (TaskSpec domain)
