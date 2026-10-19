# ADR-0027: Firebase Cloud Messaging Plus Supabase Trigger for Push Notifications

## Status
accepted

## Context
Push delivery needs a reliable transport plus a programmable trigger bound to data changes.

## Decision
Use Firebase Cloud Messaging for delivery and a Supabase database trigger to enqueue pushes from row changes.

## Consequences

### Positive
- FCM handles device registration, delivery, and QoS on both platforms.
- Supabase trigger keeps push logic close to the data model.
- No extra worker tier needed for most flows.

### Negative
- FCM quota limits must be managed for large fan-out.
- Trigger code runs in Postgres and must be kept small.

### Neutral
- Fan-out heavy flows can be redirected to a Fly worker (ADR-0025).

## Alternatives Considered
- OneSignal (rejected: added vendor overlap).
- Custom push gateway (rejected: device token lifecycle complexity).

## Related
- ADR-0024
- ADR-0025
