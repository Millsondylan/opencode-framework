# Runbook: Play Track Rollback via Halt and Previous Release

## Purpose
Roll back a Play track to the previous known-good version by halting the current rollout and republishing the prior AAB.

## Prerequisites
- Play Console access with the release manager role.
- Previous AAB archived in Cloudflare R2 under the release bucket.
- Keychain entries for signing key alias and keystore password.
- On-call engineer paged and aware the rollback is in progress.

## Procedure
1. Open the Play Console and navigate to the affected track.
2. Click Halt rollout on the current release to stop further delivery.
3. Create a new release on the same track using the previous AAB from R2.
4. Set the release notes to reference the rollback and the original issue id.
5. Submit the release with staged rollout at 10 percent.
6. Monitor crash-free user rate for 30 minutes before ramping further.
7. Ramp to 50 percent, then to 100 percent once the crash-free rate stabilizes.
8. Record the rollback in docs/decisions with the halt timestamp and rollback AAB version.

## Verification
- Halt takes effect within five minutes of click (Play Console status).
- Crash-free user rate returns to pre-incident levels within 60 minutes.
- Previous AAB is the only active build on the target track.
- Sentry releases dashboard reflects the rollback version as current.

## Rollback
1. If the rollback itself regresses, halt the rollback release.
2. Contact Google Play support via the priority queue for emergency pull.
3. Disable Shorebird patches that may be masking or worsening the issue.
4. Update docs/open-items.md with the active incident status.

## Escalation
- Primary: release captain.
- Secondary: incident commander from PagerDuty rotation.
- Tertiary: executive sponsor if user-visible impact exceeds four hours.

## Related ADRs
- ADR-0019
- ADR-0023
