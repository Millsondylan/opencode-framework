# ADR-0008: macOS Keychain Plus age-Encrypted iCloud Backup for Secrets

## Status
accepted

## Context
Secrets in dotfiles, env files, and repos leak and cannot be rotated cleanly.

## Decision
Store runtime secrets in macOS Keychain; any off-device backup must be encrypted with age using a cold-stored identity.

## Consequences

### Positive
- Zero real credentials on disk in the working tree.
- iCloud backup is cryptographically protected end to end.
- Rotation has a documented 24-hour window and decision record.

### Negative
- Developers must run the with-secrets wrapper for every command.
- Windows and Linux require a different store (CI uses provider secrets).

### Neutral
- CI fallback uses GitHub, Vercel, Doppler, AWS, GCP, or Vault natively.

## Alternatives Considered
- Dotenv files for dev (rejected: frequent leaks and no rotation).
- Single cloud vault for all secrets (rejected: online dependency).

## Related
- .claude/rules/12-keychain.md
- scripts/with-secrets.sh
