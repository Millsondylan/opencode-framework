---
name: performance-agent
description: Image caching, lazy loading, widget rebuild optimization, shader warmup
---

# performance-agent - Performance Optimization

Configures image caching, lazy loading, widget rebuild optimization, and shader warmup. Produces performance recommendations and config.

## Usage
```
/performance-agent
```

## Parameters
- None. This skill produces performance artifacts.

## What It Does
1. Configures **image caching** (cached_network_image, cache manager)
2. Implements **lazy loading** patterns (ListView.builder, pagination)
3. Applies **widget rebuild optimization** (const, keys, selectors)
4. Configures **shader warmup** — precompile shaders to avoid jank
5. Outputs **performance recommendations** — best practices doc
6. Outputs **shader warmup list** — shaders to precompile
7. Outputs **image caching config** — cache policy and setup

## Output
- Performance recommendations — optimization guide
- Shader warmup list — shaders to precompile
- Image caching config — cache manager configuration

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)

## Tech Stack
- **Images:** cached_network_image, flutter_cache_manager
- **Lists:** ListView.builder, lazy loading
- **Shaders:** Flutter shader warmup
- **Platform:** Flutter/Dart (mobile)
