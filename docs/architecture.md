# Architecture Decision Records

This file is the authoritative index of architectural decisions for the framework. Each ADR below captures a ratified decision in compact form. Full Michael Nygard bodies live in `docs/decisions/NNNN-short-title.md`, one file per decision. The short summary per entry here is the authoritative statement of the decision's intent, context, and chief consequence. For the long form context, alternatives, and rollback plan, open the linked record.

## System Overview

```
+----------------------------------------------------------------------+
|                         User Request                                 |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                     Orchestrator (main session)                      |
|  read models.yaml, enforce operating rules, single Task dispatch     |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                  16-Stage Sequential Pipeline                        |
|                                                                      |
|  -2 pipeline-scaler  -> -1 prompt-optimizer  -> 0 task-breakdown     |
|      -> 0+ user confirm -> 1 code-discovery -> 2 plan-agent          |
|      -> 3 docs-researcher -> 3.5 pre-flight-checker                  |
|      -> 4 build-agent-N -> 4.5 test-writer -> 5 debugger             |
|      -> 5.5 logical-agent -> 6 test-agent -> 6.5 integration-agent   |
|      -> 7 review-agent -> 8 decide-agent                             |
+----------------------------------------------------------------------+
       |           |            |             |             |
       v           v            v             v             v
+-----------+ +---------+ +----------+ +-----------+ +--------------+
|  Memory   | |Publish  | |Screenshots| |Marketing  | | Telemetry    |
| LanceDB   | |Play, CWS| | real UI + | |Outreach + | | PostHog EU + |
| hybrid    | |API + UI | | gen frame | | content   | | launchd logs |
+-----------+ +---------+ +----------+ +-----------+ +--------------+
       |           |            |             |             |
       +-----------+-----+------+-------+-----+------+------+
                         |              |            |
                         v              v            v
+----------------------------------------------------------------------+
|                       External Services                              |
|                                                                      |
|  Supabase (OLTP + RLS) . Cloudflare (Pages, Workers, R2)             |
|  Google Play Console (API v3 + UI) . Apple Connect                   |
|  Chrome Web Store . Fly.io (workers) . Firebase FCM                  |
|  RevenueCat . PostHog EU . GitHub . Shorebird                        |
|  Spacemail Insight MCP (sole email transport)                        |
+----------------------------------------------------------------------+
                              ^
                              |
+----------------------------------------------------------------------+
|               Daemons (launchd, KeepAlive=true)                      |
|                                                                      |
|   fsnotify file-watcher (250ms debounce, 30s poll fallback)          |
|   memory-indexer . telemetry-rollup . release-publisher              |
+----------------------------------------------------------------------+
```

The orchestrator stays in a strict single-dispatch loop, driving one subagent per response across the 16 ordered stages. Subsystems (memory, publishing, screenshots, marketing, telemetry) run as independent modules invoked from pipeline stages or from scheduled launchd daemons. All email routes through the Spacemail Insight MCP. All secrets live in macOS Keychain with age-encrypted iCloud backup.

## Component Map

| Subsystem | Path | Purpose |
|-----------|------|---------|
| Orchestrator rules | `.claude/rules/` | Stage ordering, confidence gate, operating rules |
| Agents | `.claude/agents/` | 80+ subagent definitions, each with semver frontmatter |
| Skills | `.claude/skills/` | 126+ domain skills loaded per plan batch |
| Memory | `memory/` | LanceDB store, embedders, rerankers, dedup, TTL pruner |
| Publishing | `publishing/` | Play API v3 driver, Chrome automator, release manifests |
| Screenshots | `screenshots/` | Real UI capture scripts plus Claude-generated frames |
| Marketing | `marketing/` (planned) | Outreach swarm, content generators, warmup schedulers |
| Telemetry | `docs/` plus launchd jobs | Event rollups, golden suites, compliance scans |

## ADR Format

Every ADR follows the five-section Michael Nygard template:

1. Title: a short descriptive phrase prefixed with ADR-NNNN (four-digit zero-padded number).
2. Status: one of `proposed`, `accepted`, `deprecated`, or `superseded by ADR-NNNN`.
3. Context: the forces at play, constraints, and the problem being solved.
4. Decision: the choice made, stated in the active voice.
5. Consequences: the results of the decision, both positive and negative, including follow-on obligations.

Canonical file location for full bodies: `docs/decisions/NNNN-short-title.md`. The number is zero-padded to four digits. The short-title is lowercase kebab-case.

Status values:

- `proposed`: drafted but not yet ratified.
- `accepted`: ratified and in force.
- `deprecated`: no longer recommended but not replaced.
- `superseded by ADR-NNNN`: replaced by a newer decision; include the replacing ADR number.

## Index of Decisions

| ADR Number | Title | Status |
|------------|-------|--------|
| ADR-0001 | Pipeline Stage Ordering and 16-Stage Flow | accepted |
| ADR-0002 | Two-Tier Model Routing (Opus 4.7 Critical, Sonnet 4.6 Standard) | accepted |
| ADR-0003 | Confidence-Based Model Escalation at Threshold 0.75 | accepted |
| ADR-0004 | Em-Dash and En-Dash Ban Across All Outputs | accepted |
| ADR-0005 | Spacemail Insight MCP as Sole Email Transport | accepted |
| ADR-0006 | RLS Enabled on Every Supabase Table | accepted |
| ADR-0007 | security_invoker Enabled on Every Supabase View | accepted |
| ADR-0008 | macOS Keychain Plus age-Encrypted iCloud Backup for Secrets | accepted |
| ADR-0009 | Multi-Critic PR Gate at Score 95 Production, 85 Hackathon | accepted |
| ADR-0010 | Decision Records to docs/decisions/YYYY-MM-DD.md per Stage | accepted |
| ADR-0011 | Confidence Score 0 to 100 Appended to Every Completion | accepted |
| ADR-0012 | Full Autonomy via bypassPermissions; Blockers Parked in open-items.md | accepted |
| ADR-0013 | launchd KeepAlive=true and ThrottleInterval=30 for Long-Running Work | accepted |
| ADR-0014 | File Watcher via fsnotify with 250ms Debounce and 30s Poll Fallback | accepted |
| ADR-0015 | Memory System on Embedded LanceDB with Hybrid BM25 Plus Dense Rerank | accepted |
| ADR-0016 | Qwen3 General and Jina Code Embedders with Jina Tiny Reranker | accepted |
| ADR-0017 | Three-Stage Dedup (SimHash, MinHash LSH, Semantic Cosine with NLI) | accepted |
| ADR-0018 | Memory TTL Tiers (7d Logs, 30d Traces, 60d Diffs, 180d Lessons) | accepted |
| ADR-0019 | Publishing Pipeline Splits Play API v3 and Chrome Automator | accepted |
| ADR-0020 | Closed Testing Requirement 12 Testers over 14 Consecutive Days | accepted |
| ADR-0021 | Android API 35 Target Plus 16 KB Memory Pages Plus Play Billing v8.3.0+ | accepted |
| ADR-0022 | Screenshot Pipeline Uses Real UI Captures Inside Claude-Generated Frames | accepted |
| ADR-0023 | Shorebird Code Push Plus in_app_update for App Update Flow | accepted |
| ADR-0024 | RevenueCat as Subscription Source of Truth, Play Developer Notifications | accepted |
| ADR-0025 | Fly.io for Long Workers, Cloudflare R2 for Blobs, Supabase for OLTP | accepted |
| ADR-0026 | Cloudflare Pages Plus Workers for Next.js Web Hosting | accepted |
| ADR-0027 | Firebase Cloud Messaging Plus Supabase Trigger for Push Notifications | accepted |
| ADR-0028 | PostHog Cloud EU with Autocapture Off as Analytics Platform | accepted |
| ADR-0029 | Agent and Skill Semver Frontmatter with Load-Time Version Check | accepted |
| ADR-0030 | Project Bootstrap Script Creates Repo Plus Supabase Plus Cloudflare Plus GitHub Plus Keychain | accepted |

## ADR-0001: Pipeline Stage Ordering and 16-Stage Flow

Status: accepted. Every request flows through a fixed 16-stage sequence from pipeline-scaler through decide-agent with exactly one subagent dispatch per response. Stage order is immutable, mandatory stages never skip, and conditional stages (build, test-writer, logical-agent, test-agent, integration-agent) skip only when the plan has no files to implement. Full record: [docs/decisions/0001-pipeline-stage-ordering-and-16-stage-flow.md](decisions/0001-pipeline-stage-ordering-and-16-stage-flow.md).

## ADR-0002: Two-Tier Model Routing (Opus 4.7 Critical, Sonnet 4.6 Standard)

Status: accepted. Stages are routed to exactly two tiers declared in `models.yaml`: `tier_critical` (`claude-opus-4-7`) for plan, build, debugger, logical, review, decide, and critics, and `tier_standard` (`claude-sonnet-4-6`) for everything else. No stage hardcodes a model string; the orchestrator resolves the tier at dispatch time. Full record: [docs/decisions/0002-two-tier-model-routing.md](decisions/0002-two-tier-model-routing.md).

## ADR-0003: Confidence-Based Model Escalation at Threshold 0.75

Status: accepted. A `tier_standard` stage is promoted to `tier_critical` when the agent self-reports confidence below 0.75 or the stage is explicitly tagged `critical` by the caller or plan. Downgrade back to standard is allowed only after three consecutive runs at or above 0.90 confidence, with a warning logged on every downgrade. Full record: [docs/decisions/0003-confidence-based-model-escalation.md](decisions/0003-confidence-based-model-escalation.md).

## ADR-0004: Em-Dash and En-Dash Ban Across All Outputs

Status: accepted. The characters U+2014, U+2013, U+2012, and U+2015 are forbidden in every output, file, commit message, comment, and string; only ASCII hyphen-minus (U+002D), colon, comma, and period are permitted as substitutes. The ban is enforced by a `pre_tool_use.py` scan on every write plus a `review-agent` scan, with any match blocking the pipeline. Full record: [docs/decisions/0004-em-dash-and-en-dash-ban.md](decisions/0004-em-dash-and-en-dash-ban.md).

## ADR-0005: Spacemail Insight MCP as Sole Email Transport

Status: accepted. All outbound email routes exclusively through `mcp__claude_ai_Spacemail_Insight__*` tools; SMTP libraries, SendGrid, Mailgun, Postmark, SES, and Resend are banned at the write, review, and CI layers. Fire-and-forget producers enqueue to a local durable queue drained by a worker that calls the MCP, with no provider fallback permitted during outages. Full record: [docs/decisions/0005-spacemail-insight-mcp-sole-email.md](decisions/0005-spacemail-insight-mcp-sole-email.md).

## ADR-0006: RLS Enabled on Every Supabase Table

Status: accepted. Every table in any application-owned schema has `ENABLE ROW LEVEL SECURITY` applied in the same migration that creates it, with explicit per-operation policies scoped to `authenticated` or `anon`. `pre-flight-checker` queries `pg_class.relrowsecurity` and fails the pipeline if any application table lacks RLS. Full record: [docs/decisions/0006-rls-enabled-on-every-table.md](decisions/0006-rls-enabled-on-every-table.md).

## ADR-0007: security_invoker Enabled on Every Supabase View

Status: accepted. Every view is created `WITH (security_invoker = on)` so that RLS policies on the underlying tables apply to the caller's JWT, not the view owner's role. Functions default to `SECURITY INVOKER`; `SECURITY DEFINER` requires an inline justification block plus a paired decision record. Full record: [docs/decisions/0007-security-invoker-on-every-view.md](decisions/0007-security-invoker-on-every-view.md).

## ADR-0008: macOS Keychain Plus age-Encrypted iCloud Backup for Secrets

Status: accepted. Every runtime secret lives in the macOS Keychain, accessed via `security find-generic-password` at exec time by a wrapper script; `.env` files may hold only placeholders. Backups that leave the machine are encrypted with `age` using recipients from `docs/keys/backup-recipients.txt`; the private key lives in offline cold storage. Full record: [docs/decisions/0008-keychain-age-encrypted-backup.md](decisions/0008-keychain-age-encrypted-backup.md).

## ADR-0009: Multi-Critic PR Gate at Score 95 Production, 85 Hackathon

Status: accepted. Every PR passes a multi-critic review (architecture, code style, completeness, consistency) with a weighted score gate at 95 in production mode and 85 in hackathon mode. The gate is implemented by the `review-agent` plus an optional `perfection-validator`, with `decide-agent` blocked from emitting COMPLETE below the threshold. Full record: [docs/decisions/0009-multi-critic-pr-gate-95-85.md](decisions/0009-multi-critic-pr-gate-95-85.md).

## ADR-0010: Decision Records to docs/decisions/YYYY-MM-DD.md per Stage

Status: accepted. Every pipeline stage writes a dated decision record under `docs/decisions/` capturing rationale, alternatives considered, and confidence. Records are append-only and cross-referenced by id from commit messages, PR descriptions, and downstream ADRs so that any architectural change has a durable paper trail. Full record: [docs/decisions/0010-decision-records-per-stage.md](decisions/0010-decision-records-per-stage.md).

## ADR-0011: Confidence Score 0 to 100 Appended to Every Completion

Status: accepted. Every agent ends its output with a `### CONFIDENCE` block scoring completeness, accuracy, evidence quality, and format compliance at 25 points each for a total of 0 to 100. The orchestrator fails and reruns the agent when score is strictly below 90 or the block is missing, and flags the pipeline when the rolling average drops below 95. Full record: [docs/decisions/0011-confidence-score-on-every-completion.md](decisions/0011-confidence-score-on-every-completion.md).

## ADR-0012: Full Autonomy via bypassPermissions; Blockers Parked in open-items.md

Status: accepted. The framework runs with `bypassPermissions` enabled so pipeline stages never pause for interactive approval; agents never ask the user questions mid-run. Unresolvable blockers are appended to `docs/open-items.md` with id, severity, owner, and mitigation, and the pipeline continues on the remaining work. Full record: [docs/decisions/0012-full-autonomy-bypass-permissions.md](decisions/0012-full-autonomy-bypass-permissions.md).

## ADR-0013: launchd KeepAlive=true and ThrottleInterval=30 for Long-Running Work

Status: accepted. All long-running framework workers (memory indexer, telemetry rollup, release publisher) run under macOS launchd plists with `KeepAlive=true` and `ThrottleInterval=30` to enforce automatic restart without thrash on crash loops. Logs route to stable paths under `~/Library/Logs/` for post-mortem analysis. Full record: [docs/decisions/0013-launchd-keepalive-throttle.md](decisions/0013-launchd-keepalive-throttle.md).

## ADR-0014: File Watcher via fsnotify with 250ms Debounce and 30s Poll Fallback

Status: accepted. The framework file watcher uses `fsnotify` for native change events with a 250ms debounce window to coalesce bursts, plus a 30s poll fallback for network filesystems and virtualized mounts where inotify-class events are unreliable. The fallback is always armed, not opt-in, so correctness survives filesystem variation. Full record: [docs/decisions/0014-fsnotify-file-watcher.md](decisions/0014-fsnotify-file-watcher.md).

## ADR-0015: Memory System on Embedded LanceDB with Hybrid BM25 Plus Dense Rerank

Status: accepted. The memory layer stores content in an embedded LanceDB instance (no separate service) and retrieves via a hybrid pipeline: BM25 for lexical recall, dense vector search for semantic recall, and a rerank stage that fuses the two before returning top-k. This keeps operations local-first while matching hosted-vector-store quality. Full record: [docs/decisions/0015-memory-lancedb-hybrid.md](decisions/0015-memory-lancedb-hybrid.md).

## ADR-0016: Qwen3 General and Jina Code Embedders with Jina Tiny Reranker

Status: accepted. General prose is embedded with Qwen3, code payloads are embedded with Jina code embedders, and retrieval results pass through a Jina tiny reranker that fits on-device. Content type drives embedder selection at ingest; the reranker is shared across both types. Full record: [docs/decisions/0016-qwen3-jina-embedders.md](decisions/0016-qwen3-jina-embedders.md).

## ADR-0017: Three-Stage Dedup (SimHash, MinHash LSH, Semantic Cosine with NLI)

Status: accepted. Memory ingestion runs a three-stage dedup cascade: SimHash for cheap near-duplicate rejection, MinHash LSH for probabilistic set-similarity filtering, and semantic cosine gated by an NLI entailment check for fine-grained semantic dedup. Each stage drops candidates at increasing cost, preserving meaningful variations while removing redundant copies. Full record: [docs/decisions/0017-three-stage-dedup.md](decisions/0017-three-stage-dedup.md).

## ADR-0018: Memory TTL Tiers (7d Logs, 30d Traces, 60d Diffs, 180d Lessons)

Status: accepted. Memory content is tiered by expected useful lifetime: logs expire after 7 days, traces after 30, diffs after 60, and distilled lessons after 180. A scheduled pruner enforces the TTLs so the store does not grow unboundedly and low-value content is evicted before high-value content. Full record: [docs/decisions/0018-memory-ttl-tiers.md](decisions/0018-memory-ttl-tiers.md).

## ADR-0019: Publishing Pipeline Splits Play API v3 and Chrome Automator

Status: accepted. Android releases use the Google Play Developer API v3 for AAB upload, track promotion, and release notes, while Chrome Web Store releases run through a headless Chrome automator since no equivalent API exists. Both tracks share metadata manifests so store listings stay consistent. Full record: [docs/decisions/0019-publishing-play-api-v3-chrome.md](decisions/0019-publishing-play-api-v3-chrome.md).

## ADR-0020: Closed Testing Requirement 12 Testers over 14 Consecutive Days

Status: accepted. New personal-account Play apps run closed testing with at least 12 opted-in testers for 14 consecutive days before production eligibility, per Google's 2024 policy. The release pipeline blocks the production track promotion until both counts are satisfied and recorded in the release manifest. Full record: [docs/decisions/0020-closed-testing-12-testers-14-days.md](decisions/0020-closed-testing-12-testers-14-days.md).

## ADR-0021: Android API 35 Target Plus 16 KB Memory Pages Plus Play Billing v8.3.0+

Status: accepted. Every Android app targets API 35, supports 16 KB memory pages, and uses Play Billing Library v8.3.0 or later to satisfy Google Play's 2025 upload requirements. Release builds verify the three pins via automated checks before AAB upload. Full record: [docs/decisions/0021-android-api-35-16kb-billing-v8.md](decisions/0021-android-api-35-16kb-billing-v8.md).

## ADR-0022: Screenshot Pipeline Uses Real UI Captures Inside Claude-Generated Frames

Status: accepted. Store-listing screenshots composite real UI captures from the running app inside Claude-generated device frames, backgrounds, and captions. Generating in-frame UI is forbidden; frames, captions, and backgrounds are always generated, never hand-edited. Full record: [docs/decisions/0022-screenshot-real-ui-claude-frames.md](decisions/0022-screenshot-real-ui-claude-frames.md).

## ADR-0023: Shorebird Code Push Plus in_app_update for App Update Flow

Status: accepted. Dart-only patches deploy via Shorebird code push for fast delivery without store review, while binary changes prompt users via Play's `in_app_update` API. The release manifest records which channel each update targets so rollouts stay auditable. Full record: [docs/decisions/0023-shorebird-code-push-in-app-update.md](decisions/0023-shorebird-code-push-in-app-update.md).

## ADR-0024: RevenueCat as Subscription Source of Truth, Play Developer Notifications

Status: accepted. RevenueCat holds the canonical subscription state read by clients and servers, with Play Developer Notifications and App Store Server Notifications wired as the authoritative server-side change feed. The client never asserts entitlement independently; all checks flow through RevenueCat's API. Full record: [docs/decisions/0024-revenuecat-subscriptions.md](decisions/0024-revenuecat-subscriptions.md).

## ADR-0025: Fly.io for Long Workers, Cloudflare R2 for Blobs, Supabase for OLTP

Status: accepted. Long-running workers run on Fly.io machines, large blobs and artifacts live in Cloudflare R2 for cheap egress-free storage, and transactional data runs on Supabase Postgres with RLS. Each workload lands on the provider whose cost and performance profile fits best, avoiding a single-cloud lock-in. Full record: [docs/decisions/0025-fly-r2-supabase-stack.md](decisions/0025-fly-r2-supabase-stack.md).

## ADR-0026: Cloudflare Pages Plus Workers for Next.js Web Hosting

Status: accepted. Next.js web apps deploy to Cloudflare Pages with Workers handling API routes and edge compute, delivering global CDN presence and zero cold-start response times under a single deployment command. This replaces Vercel and regional VMs for the framework's web tier. Full record: [docs/decisions/0026-cloudflare-pages-workers-nextjs.md](decisions/0026-cloudflare-pages-workers-nextjs.md).

## ADR-0027: Firebase Cloud Messaging Plus Supabase Trigger for Push Notifications

Status: accepted. Mobile and web push notifications deliver via Firebase Cloud Messaging; server-side fan-out is driven by Supabase triggers on relevant tables that call an edge function to invoke FCM. This keeps notification logic close to the data model without a separate notification service. Full record: [docs/decisions/0027-fcm-supabase-push.md](decisions/0027-fcm-supabase-push.md).

## ADR-0028: PostHog Cloud EU with Autocapture Off as Analytics Platform

Status: accepted. Product analytics run on PostHog Cloud EU with autocapture explicitly disabled; every event is instrumented by hand with a defined schema and PII allowlist. EU residency satisfies data-protection requirements and explicit instrumentation prevents accidental PII leakage. Full record: [docs/decisions/0028-posthog-eu-analytics.md](decisions/0028-posthog-eu-analytics.md).

## ADR-0029: Agent and Skill Semver Frontmatter with Load-Time Version Check

Status: accepted. Every agent definition and every skill carries a semver field in its YAML frontmatter; the loader validates each version against the framework's required range at session start and refuses to dispatch a mismatched component. This prevents silent breakage when agents or skills evolve on independent release cadences. Full record: [docs/decisions/0029-agent-skill-semver-frontmatter.md](decisions/0029-agent-skill-semver-frontmatter.md).

## ADR-0030: Project Bootstrap Script Creates Repo Plus Supabase Plus Cloudflare Plus GitHub Plus Keychain

Status: accepted. A single `bootstrap/bootstrap <stack> <name>` script provisions the git repo, Supabase project, Cloudflare Pages and Workers, GitHub remote, and Keychain secrets atomically for a new project, with rollback on partial failure. Manual per-provider setup is prohibited so every new project starts from identical wiring. Full record: [docs/decisions/0030-bootstrap-script-provisions-all.md](decisions/0030-bootstrap-script-provisions-all.md).

## Performance Budgets

The framework enforces the following runtime performance targets for Flutter applications generated by build-agent stages:

1. Frame budget, 60Hz display: 16.67 ms per frame (60Hz standard refresh rate for most devices).
2. Frame budget, 120Hz display: 8.33 ms per frame (120Hz ProMotion and similar high refresh displays).
3. Jank threshold: jank rate above 1 percent is noticeable to users; above 5 percent is unsatisfactory and blocks release.
4. Memory ceiling, Flutter app: 512 MB resident set size on mid-tier Android devices.
5. Cold start budget: 2.0 seconds from launch icon tap to first meaningful paint on a Pixel 6a class device.
6. Warm start budget: 800 ms from background resume to interactive.
7. APK size target: under 40 MB per ABI split; aab download size under 30 MB after Play compression.
8. Network request p95 latency: 400 ms for primary API reads, 1200 ms for writes; measured from Supabase edge regions closest to user.
9. Memory RAG recall p95 latency: 150 ms per query on M1 or later Apple Silicon; 400 ms on Intel fallback.
10. Build-agent pipeline p95 stage latency: 45 seconds per stage average across the full pipeline.

Profile all measurements in profile mode on physical devices; debug mode JIT and assertions invalidate the numbers. See `.claude/rules/07-flutter-best-practices.md` section 4 for the full performance discipline reference.
