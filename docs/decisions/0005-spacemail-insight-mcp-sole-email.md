# ADR-0005: Spacemail Insight MCP as Sole Email Transport

## Status
accepted

## Context
Direct provider SDKs fragment audit, suppression, and compliance logic across providers.

## Decision
Route every outbound message through mcp__claude_ai_Spacemail_Insight__* tools only.

## Consequences

### Positive
- Single audit trail for send, bounce, complaint, unsubscribe.
- Compliance footers and suppression list applied once, centrally.
- No SMTP or provider credentials held by application code.

### Negative
- Single point of failure requires queue absorption on outage.
- Feature parity depends on the MCP surface roadmap.

### Neutral
- Local queue drains through the MCP surface when service recovers.

## Alternatives Considered
- Provider fallback on outage (rejected: voids audit and compliance).
- Per-service SDKs (rejected: audit trail fragmentation).

## Related
- .claude/rules/13-spacemail-only.md
- ADR-0025
