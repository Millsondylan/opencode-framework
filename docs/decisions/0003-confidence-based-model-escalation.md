# ADR-0003: Confidence-Based Model Escalation at Threshold 0.75

## Status
accepted

## Context
Standard-tier agents sometimes return low-confidence outputs that need stronger reasoning.

## Decision
Auto-promote any stage to tier_critical when the agent self-reports confidence below 0.75 or the stage is tagged critical.

## Consequences

### Positive
- Low-quality responses trigger automatic retry on a stronger model.
- Human intervention not required for routine escalations.
- Downgrade after three consecutive scores at or above 0.90 reduces cost.

### Negative
- Escalation can loop if the stronger model also underperforms.
- Self-reported confidence can be gamed without anti-cheating rules.

### Neutral
- Escalation state is logged for post-run analysis.

## Alternatives Considered
- Manual escalation only (rejected: breaks autonomy rule).
- Always-on Opus for flagged stages (rejected: defeats two-tier cost model).

## Related
- .claude/rules/09-confidence-scoring.md
- ADR-0002
