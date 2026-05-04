# Runbook: Sentry Crash to Merged Fix in 10 Minutes

## Purpose
Turn a fresh Sentry issue into a merged PR within 10 minutes via the debugger agent pipeline.

## Prerequisites
- Sentry project configured with release tag on the crashed build.
- Local Keychain entry for SENTRY_AUTH_TOKEN and GH_TOKEN.
- Shorebird and Play credentials loaded via scripts/with-secrets.sh.
- Repository clean on main with no unrelated uncommitted changes.

## Procedure
1. Open the top Sentry issue and copy its short id and stack trace.
2. Run scripts/with-secrets.sh claude 'fix sentry issue <id>' to start the pipeline.
3. pipeline-scaler routes the task to a single run with critical flags.
4. code-discovery maps the affected files from the stack trace.
5. plan-agent creates a 1 to 2 file patch with test batches.
6. build-agent implements the fix and test-writer adds regression tests.
7. debugger runs the tests and fixes any residual errors.
8. review-agent checks the patch against acceptance criteria from the TaskSpec.
9. decide-agent outputs COMPLETE and opens a PR via gh pr create.

## Verification
- Sentry issue moves to resolved on next release after auto-assignment.
- CI run on the PR passes lint, unit, and integration suites.
- Coverage delta on the patch is at or above 0.85 for changed lines.
- review-agent confidence is at or above 95.

## Rollback
1. Close the PR if the diagnosis was incorrect.
2. Revert the merge commit with git revert <sha> if already merged.
3. Open a new Sentry issue reference in docs/open-items.md.
4. Notify the release channel that the rollback was published.

## Escalation
- Primary: on-call engineer via PagerDuty.
- Secondary: release captain for the affected module.
- Tertiary: security lead if the crash touches auth or payments.

## Related ADRs
- ADR-0001
- ADR-0011
