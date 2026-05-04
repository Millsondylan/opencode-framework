# ADR-0028: PostHog Cloud EU with Autocapture Off as Analytics Platform

## Status
accepted

## Context
Analytics must meet EU data-residency expectations and avoid accidental PII capture.

## Decision
Use PostHog Cloud EU with autocapture disabled and explicit event-schema definitions.

## Consequences

### Positive
- EU residency aligns with GDPR expectations for EU users.
- Disabled autocapture prevents inadvertent PII ingestion.
- Explicit schemas keep dashboards stable over time.

### Negative
- Manual event definition slows initial instrumentation.
- EU-only region limits some PostHog beta features.

### Neutral
- Event taxonomy is versioned alongside the app.

## Alternatives Considered
- Autocapture on (rejected: PII leakage risk).
- Self-hosted PostHog (rejected: operational overhead).

## Related
- ADR-0025
- ADR-0012
