---
description: "Run task-breakdown, code-discovery, and plan-agent only; output plan without implementing"
---

# /plan

Produce a batched implementation plan for a spec without writing any code. `/plan` runs the first scoping and planning stages, then stops at `plan-agent` output plus a `decide-agent` readiness check. Use this to preview scope, batch breakdown, and file impact before committing to a `/ship` run.

## Arguments

- `<spec>`: path to a spec file or inline description of the work.
- `--output <path>`: write the plan to the given path instead of stdout. Defaults to `docs/plans/<date>-<slug>.md`.
- `--verbose`: include full TaskSpec and RepoProfile alongside the plan output.

## Pipeline

Runs the plan-only subset of the 16-stage pipeline:

1. pipeline-scaler (always mandatory)
2. prompt-optimizer (optimizes the spec for task-breakdown)
3. task-breakdown (produces the TaskSpec; feature decomposition)
4. user confirmation (presents TaskSpec for approval)
5. code-discovery (produces RepoProfile: conventions, files, tech stack)
6. plan-agent (produces the batched implementation plan, 1 to 2 files per batch)
7. decide-agent (readiness check; does NOT mark as COMPLETE, only validates plan quality)

Stages 3.5 through 8 (docs-researcher through publish) are skipped. No files are written to the target project; only the plan document is produced.

## Example

```
/plan specs/feature-auth.md
/plan "refactor settings screen into separate widgets" --output docs/plans/settings-refactor.md
/plan specs/payment-flow.md --verbose
```

## Related

- ADR-0001 (pipeline stage ordering)
- `.claude/rules/02-prompt-optimization.md` for how the spec is optimized
- `.claude/rules/03-agent-dispatch.md` for the micro-batch philosophy (1 to 2 files per batch)
- `/ship` to execute the plan end to end
- `/review` to score a draft plan against critics
