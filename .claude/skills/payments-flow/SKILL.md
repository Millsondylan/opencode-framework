---
name: payments-flow
description: Implement purchase flow, restore purchases, receipt validation state management with Riverpod
---

# payments-flow - Payments Domain Flow

Implements purchase flow orchestration, restore purchases, receipt validation state management, and purchase flow providers with Riverpod. Third in the payments domain chain (3/6).

## Usage
```
/payments-flow
```

## Parameters
- None. This skill consumes payments-schema and payments-provider outputs and produces flow artifacts.

## What It Does
1. Implements **PaymentsNotifier** — Riverpod StateNotifier for payments state
2. Defines **PaymentsState** — active, expired, pending, loading, error, restoring
3. Registers **paymentsProvider** — Riverpod provider exposing PaymentsNotifier
4. Orchestrates **purchase flow** — product selection → purchase → receipt validation → entitlement update
5. Orchestrates **restore purchases** — restore request → provider sync → state refresh
6. Manages **receipt validation state** — validating, valid, invalid, retry
7. Handles **subscription status** — active, expired, grace period, billing retry
8. Coordinates with **purchase flow providers** — product list, purchase, restore, entitlements

## Output
- `payments_notifier.dart` — PaymentsNotifier (StateNotifier<PaymentsState>)
- `payments_state.dart` — PaymentsState sealed class / union type
- `payments_provider.dart` — paymentsProvider (Riverpod Provider)
- Purchase flow providers (product list, purchase, restore, entitlement check)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (payments-schema responsibility)
- Write repository or data source code (payments-provider responsibility)
- Write UI components or screens (payments-ui responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **State:** Riverpod (StateNotifier, Provider)
- **Persistence:** Hive (receipt metadata, entitlement cache, if needed)
- **Backend:** Supabase (via payments-provider repository)
- **Architecture:** Clean Architecture (presentation/application layer)
- **Domain:** payments (TaskSpec domain)
