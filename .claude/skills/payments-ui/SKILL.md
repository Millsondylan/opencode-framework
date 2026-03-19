---
name: payments-ui
description: Implement paywall screen, subscription management, transaction history UI with Material 3
---

# payments-ui - Payments Domain UI

Implements paywall screen, subscription management screens, and transaction history UI with Material 3. Fourth in the payments domain chain (4/6).

## Usage
```
/payments-ui
```

## Parameters
- None. This skill consumes payments-flow outputs and produces UI artifacts.

## What It Does
1. Implements **PaywallScreen** — product list, purchase CTA, loading state, error handling
2. Implements **subscription management screens** — current plan, upgrade/downgrade, cancel
3. Implements **transaction history** — list of past purchases, receipts, refund status
4. Adds **product cards** — plan comparison, pricing, feature highlights
5. Handles **purchase flow UI** — loading overlay, success/error feedback, restore button
6. Handles **error states** — snackbars, banners, inline error messages for purchase failures
7. Uses **Material 3** — components, theming, typography

## Output
- `paywall_screen.dart` — PaywallScreen widget
- `subscription_management_screen.dart` — Subscription management widget
- `transaction_history_screen.dart` — Transaction history widget
- Product card components (plan cards, pricing display)
- Purchase flow UI components (loading overlay, success/error feedback)

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (payments-schema responsibility)
- Write repository or data source code (payments-provider responsibility)
- Write flow/state orchestration (payments-flow responsibility)
- Write route guards or payment middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read paymentsProvider, call PaymentsNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** payments (TaskSpec domain)
