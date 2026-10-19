---
description: "Run telemetry rollup, golden suite, dash scan, and policy compliance check"
---

# /audit

Observe the framework's current state and produce a compliance report. `/audit` rolls up telemetry from PostHog and launchd logs, runs the golden suite of regression tests, scans the repo for banned dashes (ADR-0004), and checks every operating rule for violations. Output is a single compliance report with a PASS or FAIL verdict.

## Arguments

- `--since <duration>`: telemetry window, e.g. `24h`, `7d`, `30d`. Defaults to `7d`.
- `--strict`: fail on any warning, not just errors. Default treats warnings as informational.
- `--rules <glob>`: scope the policy scan to matching rule files under `.claude/rules/`. Defaults to all rules.
- `--output <path>`: write the report to the given path. Defaults to `docs/audits/<date>.md`.

## Pipeline

Runs the audit sequence:

1. telemetry rollup (PostHog EU event counts, retention, subscription deltas, launchd job durations)
2. golden suite execution (regression tests across agents, skills, and fixtures in `memory/golden/`)
3. dash scan (banned U+2014, U+2013, U+2012, U+2015 across every tracked file per ADR-0004)
4. security scan (hardcoded secret patterns per `.claude/rules/12-keychain.md`)
5. Spacemail compliance scan (no banned email libraries per `.claude/rules/13-spacemail-only.md`)
6. RLS + security_invoker coverage check against the database (ADR-0006, ADR-0007)
7. decision record integrity check (every `SECURITY DEFINER` and every RLS disable has a paired record)

## Example

```
/audit
/audit --since 30d --strict
/audit --rules '.claude/rules/1*.md' --output docs/audits/rules-10-to-13.md
```

## Related

- ADR-0004 (dash ban), ADR-0006 (RLS), ADR-0007 (security_invoker), ADR-0028 (PostHog EU)
- `.claude/rules/08-em-dash-ban.md`, `.claude/rules/10-rls.md`, `.claude/rules/11-security-invoker.md`
- `.claude/rules/12-keychain.md`, `.claude/rules/13-spacemail-only.md`
- `/review` for PR-level critic scoring (audit is framework-wide, review is PR-scoped)
- `/ship` to remediate failures found by audit
