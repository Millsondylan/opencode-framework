# ADR-0025: Fly.io for Long Workers, Cloudflare R2 for Blobs, Supabase for OLTP

## Status
accepted

## Context
Different workload shapes need different hosts and object stores.

## Decision
Run long workers on Fly.io, store blobs on Cloudflare R2, and keep OLTP on Supabase Postgres.

## Consequences

### Positive
- Each tier hosted on the right primitive for its shape.
- R2 egress pricing is favorable versus alternatives.
- Supabase provides RLS, auth, and Postgres in one surface.

### Negative
- Three-vendor stack requires matching IAM and secret rotation flows.
- Cross-cloud latency must be measured on the critical path.

### Neutral
- Observability is federated via OpenTelemetry.

## Alternatives Considered
- All-AWS stack (rejected: higher egress, weaker Supabase ergonomics).
- Single-region single-vendor (rejected: vendor lock-in risk).

## Related
- ADR-0026
- ADR-0028
