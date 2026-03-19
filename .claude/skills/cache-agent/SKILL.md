---
name: cache-agent
description: Caching — invalidation, TTL, memory vs disk
---

# cache-agent - Caching

Configures caching with invalidation, TTL, and memory vs disk policies. Produces cache infrastructure.

## Usage
```
/cache-agent
```

## Parameters
- None. This skill produces cache artifacts.

## What It Does
1. Implements **cache manager** — get, set, invalidate
2. Configures **invalidation** — time-based, event-based
3. Configures **TTL** (time-to-live) policies
4. Configures **memory vs disk** — L1 (memory), L2 (disk)
5. Outputs **lib/core/cache/** — cache module
6. Outputs **cache manager** — cache implementation
7. Outputs **TTL policies** — expiration configuration

## Output
- `lib/core/cache/` — Cache module
- Cache manager — cache implementation
- TTL policies — expiration and invalidation configuration

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write repository implementations (cache infrastructure only)

## Tech Stack
- **Cache:** In-memory, disk (Hive, file)
- **TTL:** Time-to-live, expiration
- **Architecture:** Clean Architecture (data layer)
- **Platform:** Flutter/Dart (mobile)
