# ADR-0012: Full Autonomy via bypassPermissions, Blockers Parked in open-items.md

## Status
accepted

## Context
Interactive prompts during long pipelines halt progress and erode throughput.

## Decision
Run in bypassPermissions mode and never ask the user; when blocked, log to docs/open-items.md and continue.

## Consequences

### Positive
- End-to-end runs complete without human intervention.
- Blockers are explicit, centralized, and tractable.
- Safety rails are preserved through hooks, not prompts.

### Negative
- A malformed plan can do more harm before detection.
- Requires strong pre-write hooks for security and correctness.

### Neutral
- User confirmation still happens once after task-breakdown.

## Alternatives Considered
- Prompted approval at every destructive step (rejected: velocity loss).
- Full dry-run mode (rejected: forks execution semantics).

## Related
- docs/open-items.md
- CLAUDE.md
