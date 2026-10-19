# ADR-0020: Closed Testing Requirement 12 Testers over 14 Consecutive Days

## Status
accepted

## Context
Google requires personal developer accounts to complete a closed test with 12 testers for 14 days before production.

## Decision
Every new Play release from a personal account must complete closed testing with at least 12 active testers for 14 consecutive days.

## Consequences

### Positive
- Matches Google policy exactly, avoiding rejection at promotion.
- Tester tracking is automated via invite and audit queries.
- Release calendar reflects the real fastest path to production.

### Negative
- Adds a minimum two-week delay to first production release.
- Tester churn can reset eligibility.

### Neutral
- Business-account publications are exempt and tracked separately.

## Alternatives Considered
- Skip closed testing (rejected: Google policy violation).
- Internal testing only (rejected: insufficient for production eligibility).

## Related
- docs/runbooks/release.md
- ADR-0019
