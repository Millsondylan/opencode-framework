---
name: dependency-agent
description: pub.dev packages, version pinning, conflict resolution
---

# dependency-agent - Dependency Management

Manages pub.dev packages, version pinning, and conflict resolution. Produces pubspec.yaml with version constraints and conflict reports.

## Usage
```
/dependency-agent
```

## Parameters
- None. This skill produces dependency artifacts.

## What It Does
1. Adds/updates **pub.dev packages** in pubspec.yaml
2. Applies **version pinning** (exact, caret, range)
3. Resolves **dependency conflicts** (version constraints)
4. Outputs **pubspec.yaml** — package list and versions
5. Outputs **version constraints** — dependency_overrides if needed
6. Outputs **conflict report** — unresolved conflicts and recommendations

## Output
- `pubspec.yaml` — Package dependencies and versions
- Version constraints — dependency_overrides
- Conflict report — unresolved conflicts and recommendations

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)

## Tech Stack
- **Package manager:** pub
- **Registry:** pub.dev
- **Platform:** Flutter/Dart
