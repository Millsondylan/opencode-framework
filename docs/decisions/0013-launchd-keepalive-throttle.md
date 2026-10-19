# ADR-0013: launchd KeepAlive true and ThrottleInterval 30 for Long-Running Work

## Status
accepted

## Context
Long workers die from resource pressure and need automatic recovery without tight restart loops.

## Decision
Register long-running jobs under macOS launchd with KeepAlive true and ThrottleInterval 30 seconds.

## Consequences

### Positive
- Crashed workers restart automatically.
- Throttle prevents CPU spin during repeated early failures.
- launchd logs provide a consistent failure view.

### Negative
- macOS-only; linux targets need systemd equivalents.
- ThrottleInterval delays recovery from transient errors.

### Neutral
- plists live in ~/Library/LaunchAgents with version control stubs.

## Alternatives Considered
- nohup and shell loops (rejected: no crash telemetry).
- pm2 (rejected: extra dependency for minimal gain on macOS).

## Related
- docs/runbooks/release.md
- ADR-0014
