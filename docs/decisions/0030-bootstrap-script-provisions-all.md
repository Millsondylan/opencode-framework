# ADR-0030: Project Bootstrap Script Creates Repo Plus Supabase Plus Cloudflare Plus GitHub Plus Keychain

## Status
accepted

## Context
New projects need repeatable provisioning of every dependency before the first commit.

## Decision
A single bootstrap script creates the GitHub repo, Supabase project, Cloudflare assets, Keychain items, and seed files in one run.

## Consequences

### Positive
- One command produces a running skeleton.
- Every artifact is named by policy, not by accident.
- Secret items land in Keychain rather than env files.

### Negative
- Bootstrap script must track provider API changes.
- Partial failures need idempotent retry logic.

### Neutral
- Script is covered by a runbook for manual recovery.

## Alternatives Considered
- Manual provisioning (rejected: inconsistent per project).
- Terraform only (rejected: does not cover Keychain or GitHub repo init).

## Related
- ADR-0008
- ADR-0025
