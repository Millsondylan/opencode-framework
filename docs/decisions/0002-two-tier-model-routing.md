# ADR-0002: Two-Tier Model Routing (Opus 4.7 Critical, Sonnet 4.6 Standard)

## Status
accepted

## Context
Mixing models across stages controls cost while preserving quality where it matters.

## Decision
Route critical stages to claude-opus-4-7 and standard stages to claude-sonnet-4-6 via models.yaml.

## Consequences

### Positive
- Cost reduced on discovery, research, and pre-flight stages.
- Critical reasoning retained for plan, build, debug, review, decide.
- Single source of truth in models.yaml prevents drift.

### Negative
- Two-model setup increases test matrix size.
- Model version drift requires periodic yaml updates.

### Neutral
- Both tiers share the same tool surface and prompt format.

## Alternatives Considered
- Opus everywhere (rejected: cost prohibitive for high-volume stages).
- Sonnet everywhere (rejected: quality regressions on planning).

## Related
- models.yaml
- ADR-0003
