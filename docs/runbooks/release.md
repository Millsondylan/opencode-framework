# Runbook: Build, Critic, and Promote Android Release

## Purpose
Produce a signed AAB, pass the critic gate at 95, and promote the build across Play tracks.

## Prerequisites
- Keychain entries for signing key alias and keystore password.
- Play Console access with the release manager role on the target app.
- Closed testing tester list with at least 12 active testers (ADR-0020).
- Local flutter and android build toolchains at the pinned versions.

## Procedure
1. Check out the release branch and confirm the pinned versions with scripts/check_agent_versions.py.
2. Run scripts/with-secrets.sh flutter build appbundle --release --obfuscate --split-debug-info=./debug-info/.
3. Run the critic gate via the multi-critic agent; require a score of 95 or higher.
4. Upload the AAB to the internal track via the Play Developer API v3.
5. Promote from internal to closed after smoke testing on two physical devices.
6. Collect closed testing feedback over the required 14 consecutive days.
7. Promote from closed to production with a staged rollout at 10 percent.
8. Ramp the rollout to 100 percent over 72 hours unless a halt signal fires.

## Verification
- Critic gate score is 95 or higher with all four dimensions at 20 or higher.
- Play Console shows the build on the target track with the expected version name.
- Crash-free user rate is at or above 0.995 during the staged rollout window.
- Subscription flows work on a physical device using Play Billing v8.

## Rollback
1. Halt the rollout from the Play Console if crash-free rate drops below 0.99.
2. Follow docs/runbooks/rollback.md to publish the previous good version.
3. Open an incident record in docs/decisions with root cause and mitigation.
4. Disable Shorebird patches that may have caused the regression (ADR-0023).

## Escalation
- Primary: release captain.
- Secondary: Android platform owner.
- Tertiary: Google Play support via the priority queue.

## Related ADRs
- ADR-0019
- ADR-0021
