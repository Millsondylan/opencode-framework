---
name: notif-guard
description: Implement rate limiting, quiet hours, and permission management for the notifications domain
---

# notif-guard - Notifications Domain Guard

Implements rate limiting, quiet hours enforcement, and permission management for notifications. Fifth in the notifications domain chain (5/6).

## Usage
```
/notif-guard
```

## Parameters
- None. This skill consumes notif-schema and notif-provider outputs and produces guard artifacts.

## What It Does
1. Implements **NotificationGuard** — central guard that gates notification delivery based on rules
2. Implements **rate limiting** — caps notification frequency per channel (e.g., max N per hour)
3. Implements **quiet hours** — blocks or defers notifications during configured time windows
4. Implements **permission checks** — verifies push/local notification permissions before delivery
5. Integrates with Riverpod notification state for guard decisions
6. Handles deferral and batching when guards block immediate delivery

## Output
- `notification_guard.dart` — NotificationGuard for delivery gating
- `notification_rate_limiter.dart` — Rate limiting logic
- `notification_quiet_hours.dart` — Quiet hours enforcement
- `notification_permission_checker.dart` — Permission verification before delivery

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (notif-schema responsibility)
- Write provider/repository code (notif-provider responsibility)
- Write flow/state orchestration (notif-flow responsibility)
- Write UI components or screens
- Write tests (notif-test responsibility)

## Tech Stack
- **State:** Riverpod (reads notification state for guard decisions)
- **Storage:** Hive (quiet hours config, rate limit counters)
- **Backend:** Supabase (preference sync if needed)
- **UI:** Material 3 (permission prompt integration)
- **Architecture:** Clean Architecture (presentation/guard layer)
- **Domain:** notifications (TaskSpec domain)
