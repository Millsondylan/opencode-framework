# ADR-0018: Memory TTL Tiers (7d Logs, 30d Traces, 60d Diffs, 180d Lessons)

## Status
accepted

## Context
Storing everything forever bloats the index and reduces retrieval quality.

## Decision
Apply tiered TTLs: 7 days for raw logs, 30 days for traces, 60 days for diffs, 180 days for distilled lessons.

## Consequences

### Positive
- Index size stays bounded over time.
- High-value lessons persist longer than raw events.
- Purge cadence aligns with debugging recency needs.

### Negative
- Incident forensics older than 7 days lack raw log detail.
- TTL tuning may require adjustment for specific projects.

### Neutral
- Lessons are distilled by a summarization job before lower tiers expire.

## Alternatives Considered
- Uniform 90-day TTL (rejected: either loses lessons or keeps noise).
- Infinite retention (rejected: degrades retrieval precision).

## Related
- ADR-0015
- ADR-0017
