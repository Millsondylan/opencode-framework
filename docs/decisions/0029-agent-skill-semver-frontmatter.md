# ADR-0029: Agent and Skill Semver Frontmatter with Load-Time Version Check

## Status
accepted

## Context
Agents and skills evolve and callers need to detect incompatible versions at load time.

## Decision
Each agent and skill declares a semver in frontmatter and the loader enforces compatibility against declared requirements.

## Consequences

### Positive
- Incompatible changes surface immediately at load.
- Callers can pin exact or compatible versions.
- Upgrades have a documented deprecation path.

### Negative
- Every edit must consider version impact.
- Loader must be kept in sync with semver rules.

### Neutral
- CI asserts version fields exist and parse.

## Alternatives Considered
- No versioning (rejected: silent breaking changes).
- Date-based versions (rejected: weaker compatibility semantics).

## Related
- scripts/check_agent_versions.py
- scripts/upgrade_agents_skills.py
