# ADR-0001: Pipeline Stage Ordering and 16-Stage Flow

## Status
accepted

## Context
The framework dispatches many specialized agents and needs a strict, auditable order for quality gates and handoff.

## Decision
Adopt a 16-stage sequential pipeline from pipeline-scaler through decide-agent with one Task call per response.

## Consequences

### Positive
- Predictable handoff between agents with full context inheritance.
- Gate points at every stage enable confidence scoring.
- Sequential execution eliminates race conditions in shared state.

### Negative
- Total wall-clock time is higher than a parallel design.
- A single stall blocks all downstream stages.

### Neutral
- Stages can be skipped only when the plan has no files to implement.

## Alternatives Considered
- Parallel agent fan-out (rejected: race conditions and context loss).
- Monolithic single agent (rejected: no stage-level verification).

## Related
- .claude/rules/01-pipeline-orchestration.md
- ADR-0010
