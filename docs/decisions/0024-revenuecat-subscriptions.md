# ADR-0024: RevenueCat as Subscription Source of Truth, Play Developer Notifications

## Status
accepted

## Context
Subscription state across platforms and store receipts must reconcile in one place.

## Decision
Use RevenueCat as the subscription source of truth and subscribe to Play Developer Notifications for event-driven updates.

## Consequences

### Positive
- Unified entitlement model across Android and iOS.
- Webhook-driven updates replace expensive polling.
- Dashboards show churn, MRR, and refunds in one view.

### Negative
- External dependency with its own outage modes.
- Per-active-user pricing grows with scale.

### Neutral
- Can be replaced by a direct integration later without schema churn.

## Alternatives Considered
- Direct store APIs (rejected: heavy reconciliation burden).
- Custom receipt validator (rejected: long-tail edge cases).

## Related
- ADR-0021
- ADR-0027
