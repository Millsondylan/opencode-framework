# ADR-0014: File Watcher via fsnotify with 250ms Debounce and 30s Poll Fallback

## Status
accepted

## Context
File events must arrive quickly without flooding handlers, and some filesystems drop events.

## Decision
Use fsnotify with a 250ms debounce window and a 30-second polling fallback for dropped events.

## Consequences

### Positive
- Low latency on healthy filesystems via native events.
- Debounce absorbs editor save bursts without handler thrash.
- Polling fallback catches missed events on NFS and iCloud paths.

### Negative
- Poll adds a steady low-rate IO load.
- Debounce window delays the fastest legitimate update.

### Neutral
- Both values are configurable per deployment.

## Alternatives Considered
- Pure polling (rejected: poor latency at busy hours).
- No debounce (rejected: handler amplification).

## Related
- ADR-0013
- scripts/sync-framework-to-work-tree.sh
