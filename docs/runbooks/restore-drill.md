# Runbook: Supabase PITR Restore Drill

## Purpose
Exercise point-in-time recovery on Supabase with a 14-day retention window and a four-hour recovery time objective.

## Prerequisites
- Supabase project with PITR enabled on the Pro plan or higher.
- Service-role key stored in Keychain under com.example.myapp.supabase_service_role.
- Staging Supabase project reserved for restore targets.
- psql client installed locally.

## Procedure
1. Select a target recovery point no older than 14 days.
2. Open the Supabase dashboard, navigate to Database then Backups then PITR.
3. Click Restore and pick the target timestamp to the second.
4. Choose the staging project as the restore target, not production.
5. Wait for the restore to finish; observe the status badge until Ready.
6. Connect to the staging project with psql and run the row-count queries.
7. Compare row counts against production baseline queries from the same timestamp.
8. Record any drift in docs/decisions under a restore-drill record.

## Verification
- Row count per top-level table differs by no more than five rows versus baseline.
- Restored DB exposes the expected RLS policies on every user table.
- Views in the restored DB have security_invoker set on every entry.
- Total elapsed time from click to verified restore is under four hours.

## Rollback
1. Do not promote the restore target to production.
2. Shut the staging project once the drill is complete to control cost.
3. Purge any PII copied into the staging project according to retention policy.
4. Update the drill record with failures, timings, and lessons learned.

## Escalation
- Primary: database owner.
- Secondary: infrastructure lead.
- Tertiary: Supabase support for PITR-specific issues.

## Related ADRs
- ADR-0006
- ADR-0025
