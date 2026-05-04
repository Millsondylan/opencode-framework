---
description: "Run the multi-critic review gate on the current branch and emit a weighted score"
---

# /review

Invoke the multi-critic PR gate against the current branch or a specified diff. `/review` dispatches `review-agent` with the architecture, code style, completeness, and consistency critics and emits a weighted score. The gate is 95 in production mode and 85 in hackathon mode, per ADR-0009.

## Arguments

- `--hackathon`: apply the hackathon gate at 85 instead of the production gate at 95.
- `--base <ref>`: diff against the given git ref. Defaults to `main`.
- `--files <glob>`: scope the review to matching files only; otherwise every changed file is scored.
- `--strict`: additionally dispatch `perfection-validator` for a brutal second pass.

## Pipeline

Runs the review subset of the pipeline:

1. code-discovery (refresh RepoProfile for the current diff)
2. review-agent (scores against four critics: architecture, code style, completeness, consistency)
3. perfection-validator (only when `--strict` is set; returns PERFECT or FAIL)
4. decide-agent (applies the score gate; emits PASS or BLOCK)

No build, no tests, no publish. Output is a scored report plus a PASS or BLOCK verdict. On BLOCK, the report lists every failing critic with file path citations so the follow-up `/ship` run can address them.

## Example

```
/review
/review --hackathon --base develop
/review --files 'lib/auth/**' --strict
```

## Related

- ADR-0009 (multi-critic PR gate at 95 / 85)
- ADR-0011 (confidence score on every completion)
- `.claude/rules/09-confidence-scoring.md` for the scoring rubric
- `.claude/rules/01-pipeline-orchestration.md` for the perfection validation system
- `/plan` to preview scope before review
- `/ship` to run the full pipeline including review as stage 15
