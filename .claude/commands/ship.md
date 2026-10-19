---
description: "Run the full 16-stage pipeline from scaler to Play production release"
---

# /ship

Execute the full production pipeline on a spec. `/ship` drives every stage from `pipeline-scaler` through `decide-agent` and, on a passing `COMPLETE`, continues into the publish and release tracks so the artifact reaches Play production (or the configured stores). This is the single command for shipping a feature or an app end to end.

## Arguments

- `<spec>`: path to a spec file or inline description of the work. The orchestrator routes this through `prompt-optimizer` before `task-breakdown`.
- `--hackathon`: lower the multi-critic PR gate from 95 to 85 for velocity-first runs. Defaults off (production gate 95).
- `--track <track>`: Play track override, one of `internal`, `closed`, `open`, `production`. Defaults to `production`.
- `--skip-publish`: stop after `decide-agent` COMPLETE; do not invoke the publish track.

## Pipeline

Runs all 16 pipeline stages in order with a single Task dispatch per response:

1. pipeline-scaler -> prompt-optimizer -> task-breakdown -> user confirmation
2. code-discovery -> plan-agent -> docs-researcher -> pre-flight-checker
3. build-agent-N (conditional) -> test-writer -> debugger -> logical-agent
4. test-agent -> integration-agent -> review-agent -> decide-agent

On `decide-agent` COMPLETE, and unless `--skip-publish` is set:

5. release-candidate packaging (AAB build, obfuscation, signing)
6. Play API v3 upload to the configured track (see ADR-0019, ADR-0020, ADR-0021)
7. Closed testing gate enforcement when track is `production` (12 testers, 14 days)
8. Store listing sync (screenshots, changelog, release notes)

## Example

```
/ship specs/feature-auth.md
/ship specs/hackathon-demo.md --hackathon --track internal
/ship "add dark mode toggle to settings" --skip-publish
```

## Related

- ADR-0001 (pipeline stage ordering), ADR-0009 (multi-critic gate), ADR-0019 (publishing split)
- `.claude/rules/01-pipeline-orchestration.md` for the strict sequential dispatch rule
- `/plan` for the spec-to-plan phase without implementation
- `/publish` for release-only runs on an already-built artifact
