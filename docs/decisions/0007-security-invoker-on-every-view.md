# ADR-0007: security_invoker Enabled on Every Supabase View

## Status
accepted

## Context
Views default to definer semantics so the owner bypasses RLS on underlying tables.

## Decision
Every CREATE VIEW and CREATE OR REPLACE VIEW must include WITH (security_invoker = on).

## Consequences

### Positive
- Views inherit the caller JWT and RLS policies automatically.
- Eliminates a common Supabase authorization bypass.
- Auditable via pg_class.reloptions across the schema.

### Negative
- Requires Postgres 15 or later for full support.
- Materialized views need a wrapper invoker view for tenant filtering.

### Neutral
- Functions default to SECURITY INVOKER with explicit annotation required.

## Alternatives Considered
- Owner-restricted view grants (rejected: complex and easy to miss).
- Never use views on user data (rejected: loses ergonomics).

## Related
- .claude/rules/11-security-invoker.md
- ADR-0006
