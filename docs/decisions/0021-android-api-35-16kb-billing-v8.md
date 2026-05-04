# ADR-0021: Android API 35 Target Plus 16 KB Memory Pages Plus Play Billing v8.3.0

## Status
accepted

## Context
Google requires API 35 targeting, 16 KB memory page support, and a current Play Billing library for new and updated releases.

## Decision
Target Android API 35, enable 16 KB memory page alignment, and ship with Play Billing Library v8.3.0.

## Consequences

### Positive
- Eligible for Play production and update windows.
- Forward compatible with upcoming device memory layouts.
- Newer billing API exposes current purchase and subscription flows.

### Negative
- Older build tooling needs upgrade across every module.
- Some native libraries lack 16 KB-aligned releases and need substitution.

### Neutral
- CI asserts these values on every build via Gradle checks.

## Alternatives Considered
- API 34 target (rejected: future Play blocks at policy deadline).
- Older Billing client (rejected: loses required purchase signals).

## Related
- ADR-0023
- ADR-0024
