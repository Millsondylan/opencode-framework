# ADR-0011: Confidence Score 0 to 100 Appended to Every Completion

## Status
accepted

## Context
Without a numeric self-assessment the orchestrator cannot gate or escalate automatically.

## Decision
Every agent completion ends with a CONFIDENCE block scoring four dimensions summing to 0 to 100 with a justification.

## Consequences

### Positive
- Automatic rerun below 90 without human review.
- Rolling average across a pipeline exposes systemic quality issues.
- Score supports model escalation decisions per ADR-0003.

### Negative
- Score inflation is possible without strict anti-cheating rules.
- Every agent output grows by a small fixed block.

### Neutral
- Block format is defined in rule 09, not in orchestrator rules.

## Alternatives Considered
- Human rubric review (rejected: breaks autonomy).
- Pass/fail only (rejected: loses signal needed for escalation).

## Related
- .claude/rules/09-confidence-scoring.md
- ADR-0003
