# ADR-0006: RLS Enabled on Every Supabase Table

## Status
accepted

## Context
Supabase exposes every table through PostgREST, so missing RLS equals public data.

## Decision
Every CREATE TABLE in migrations must be followed by ENABLE ROW LEVEL SECURITY with explicit per-operation policies.

## Consequences

### Positive
- Authorization enforced in the database engine, not the app layer.
- Multi-tenant isolation survives application-layer bugs.
- Policies are auditable via pg_policies at any time.

### Negative
- Every new table adds at least four policy statements.
- Service-role backfills require careful scoping.

### Neutral
- FORCE ROW LEVEL SECURITY is required when the owner is also a tenant.

## Alternatives Considered
- App-layer authorization only (rejected: framework CVEs bypass it).
- RLS on a subset of tables (rejected: inevitable oversight).

## Related
- .claude/rules/10-rls.md
- ADR-0007
