---
description: "Run the marketing stage swarm: warmup, outreach, content, and campaign launch"
---

# /market

Launch the marketing subsystem for a project. `/market` runs the outreach swarm defined under `marketing/outreach/` plus the content generators, starting with a mailbox warmup phase and escalating to a full campaign. All email sends route through the Spacemail Insight MCP per ADR-0005; provider SDKs are forbidden.

## Arguments

- `<project>`: project directory or app slug the campaign targets.
- `--warmup-days <n>`: warmup duration before full send. Defaults to 14.
- `--campaign <name>`: campaign id to launch (looked up in `marketing/campaigns/<name>.yaml`).
- `--segment <segment>`: audience segment id from the consent ledger.
- `--dry-run`: render every email and log every target without sending.

## Pipeline

Runs the marketing swarm:

1. warmup scheduler (ramps daily volume per mailbox, respects Spacemail throttle hints)
2. outreach agent swarm (`marketing/outreach/aggressive_growth.py`): target list assembly, consent check, segment filtering
3. content generation (subject line, plain text, HTML body, CTA, footer with postal address)
4. consent ledger verification (GDPR, CAN-SPAM, CASL checks per rule 13)
5. Spacemail Insight MCP dispatch (`mcp__claude_ai_Spacemail_Insight__send_campaign` for bulk, `send_email` for transactional)
6. delivery telemetry rollup (bounces, complaints, opens, unsubscribes) into PostHog EU

## Example

```
/market ./apps/finance --warmup-days 14 --campaign launch-q2
/market ./apps/flashcards --segment consented_global_newsletter --campaign weekly-tips
/market ./apps/finance --dry-run --campaign reactivation
```

## Related

- ADR-0005 (Spacemail Insight MCP as sole email transport)
- ADR-0028 (PostHog EU analytics for delivery telemetry)
- `.claude/rules/13-spacemail-only.md` for the transport policy and blocked libraries
- `marketing/outreach/aggressive_growth.py` for the swarm implementation
- `/ship` for the pipeline that produces the release before marketing runs
- `/audit` for the compliance scan that verifies campaign outputs
