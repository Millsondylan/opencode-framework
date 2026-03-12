---
name: payments-guard
description: Implement entitlement checks, fraud detection, and purchase verification for the payments domain
---

# payments-guard - Payments Domain Guard

Implements entitlement checks, fraud detection, and purchase verification. Fifth in the payments domain chain (5/6).

## Usage
```
/payments-guard
```

## Parameters
- None. This skill consumes payments-schema, payments-provider, and payments-flow outputs and produces guard artifacts.

## What It Does
1. Implements **EntitlementGuard** — blocks access to premium features when entitlement is missing or expired
2. Implements **purchase verification** — validates receipts, subscription status, and entitlement claims before granting access
3. Implements **fraud checks** — detects suspicious purchase patterns, velocity limits, device fingerprint anomalies
4. Integrates with Riverpod payments state for guard decisions
5. Handles redirect flows when guards fail (e.g., to paywall screen)
6. Coordinates with PaymentsRepository for server-side verification when needed

## Output
- `entitlement_guard.dart` — EntitlementGuard for premium feature protection
- `purchase_verification.dart` — Purchase verification logic (receipt validation, entitlement claims)
- `fraud_check.dart` — FraudCheck for suspicious activity detection

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (payments-schema responsibility)
- Write provider/repository code (payments-provider responsibility)
- Write flow/state orchestration (payments-flow responsibility)
- Write UI components or screens (payments-ui responsibility)
- Write tests (payments-test responsibility)

## Tech Stack
- **State:** Riverpod (reads payments state for guard decisions)
- **Storage:** Hive (entitlement cache, fraud metadata)
- **Backend:** Supabase (server-side verification via payments-provider)
- **UI:** Material 3 (navigation integration, paywall redirect)
- **Architecture:** Clean Architecture (presentation/guard layer)
- **Domain:** payments (TaskSpec domain)
