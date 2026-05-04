# ADR-0010: Decision Records to docs/decisions/YYYY-MM-DD.md per Stage

## Status
accepted

## Context
Stages make non-trivial choices that need durable context for future debugging.

## Decision
Every stage with a non-trivial decision writes an entry to docs/decisions/YYYY-MM-DD.md with rationale, alternatives, and confidence.

## Consequences

### Positive
- Long-term memory of why a choice was made survives personnel changes.
- Rollback plans become concrete rather than implicit.
- Cross-links from commits and PRs to records are simple.

### Negative
- Extra writing overhead per stage.
- Records can drift from current state if not updated on reversal.

### Neutral
- Templates reduce the time cost of writing a record.

## Alternatives Considered
- Commit messages as the only record (rejected: too terse).
- Wiki pages (rejected: leaves the repo and loses review).

## Related
- docs/decisions
- ADR-0001
