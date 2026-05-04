# ADR-0023: Shorebird Code Push Plus in_app_update for App Update Flow

## Status
accepted

## Context
Flutter releases benefit from fast patch delivery for Dart code while native updates still go through the store.

## Decision
Use Shorebird for Dart code pushes and in_app_update for native Play-based app updates.

## Consequences

### Positive
- Dart-level bug fixes ship within minutes.
- Native updates follow store policy and review.
- User-facing update UI remains consistent via in_app_update.

### Negative
- Two update channels complicate release notes.
- Shorebird patches constrain certain native-dependent features.

### Neutral
- Rollback semantics differ between channels and are documented.

## Alternatives Considered
- Store-only updates (rejected: slow bug fix turnaround).
- Custom OTA (rejected: reinvents Shorebird at higher risk).

## Related
- ADR-0021
- docs/runbooks/rollback.md
