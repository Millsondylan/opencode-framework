# ADR-0026: Cloudflare Pages Plus Workers for Next.js Web Hosting

## Status
accepted

## Context
The web app needs edge rendering, low cold-start times, and tight integration with R2 and KV.

## Decision
Host the Next.js web app on Cloudflare Pages with Workers for server-side features and bindings to R2 and KV.

## Consequences

### Positive
- Edge execution keeps latency low globally.
- Native R2 and KV bindings avoid cross-cloud hops.
- Pages deploy pipeline integrates with GitHub out of the box.

### Negative
- Workers runtime has specific Node-compat limitations.
- Some Next.js features require Pages-specific adapters.

### Neutral
- Preview environments are automatic per branch.

## Alternatives Considered
- Vercel (rejected: weaker R2 integration and egress).
- Self-hosted Next.js on Fly (rejected: cold-start and global distribution).

## Related
- ADR-0025
- ADR-0028
