# ADR-0019: Publishing Pipeline Splits Play API v3 and Chrome Automator

## Status
accepted

## Context
Play Console API covers most release actions but some flows require a live browser.

## Decision
Use Play Developer API v3 for programmable actions and a Chrome automator for flows that still require console interaction.

## Consequences

### Positive
- Programmable release for uploads, tracks, and rollout percentages.
- Browser automation covers closed testing setup and some policy flows.
- Each path has its own retry and logging contract.

### Negative
- Two code paths to maintain.
- Browser automation is fragile to console UI changes.

### Neutral
- Automator runs under claude-in-chrome MCP tools where possible.

## Alternatives Considered
- API-only (rejected: cannot complete all current flows).
- Browser-only (rejected: slow and flaky for programmable actions).

## Related
- publishing
- ADR-0020
