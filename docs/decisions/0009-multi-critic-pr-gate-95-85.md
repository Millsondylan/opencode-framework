# ADR-0009: Multi-Critic PR Gate at Score 95 Production, 85 Hackathon

## Status
accepted

## Context
Code review quality varies across reviewers and time, and a numeric gate aligns expectations.

## Decision
Every PR must pass a multi-critic gate at 95 in production mode and 85 in hackathon mode, covering architecture, style, completeness, consistency.

## Consequences

### Positive
- Explicit quality bar that cannot be tacitly lowered.
- Hackathon mode permits velocity without removing the gate.
- Four-dimension scoring surfaces specific gaps rather than vague concerns.

### Negative
- Gate failure can block urgent fixes until re-critiqued.
- Score inflation must be actively prevented by anti-cheating rules.

### Neutral
- Rubric is shared with agents via .claude/rules/09-confidence-scoring.md.

## Alternatives Considered
- Single reviewer approval (rejected: variance too high).
- No numeric gate (rejected: relies on memory of standards).

## Related
- .claude/rules/09-confidence-scoring.md
- ADR-0011
