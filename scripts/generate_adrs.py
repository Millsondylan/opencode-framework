#!/usr/bin/env python3
"""Generate 30 ADR files and 4 runbook files.

Writes to docs/decisions/ and docs/runbooks/ relative to repo root.
All output uses ASCII hyphen-minus only. No fancy dashes permitted.
See rule 08-em-dash-ban.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Banned code points: figure dash (0x2012), en dash (0x2013),
# em dash (0x2014), horizontal bar (0x2015). Pattern built from
# escape sequences so this source file is dash-ban clean.
BANNED_CHARS = "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015))
BANNED = re.compile("[" + BANNED_CHARS + "]")


def scan(text: str, label: str) -> None:
    if BANNED.search(text):
        raise SystemExit("Banned dash in " + label)


ADRS = [
    {
        "n": 1,
        "slug": "pipeline-stage-ordering-and-16-stage-flow",
        "title": "Pipeline Stage Ordering and 16-Stage Flow",
        "context": "The framework dispatches many specialized agents and needs a strict, auditable order for quality gates and handoff.",
        "decision": "Adopt a 16-stage sequential pipeline from pipeline-scaler through decide-agent with one Task call per response.",
        "positive": [
            "Predictable handoff between agents with full context inheritance.",
            "Gate points at every stage enable confidence scoring.",
            "Sequential execution eliminates race conditions in shared state.",
        ],
        "negative": [
            "Total wall-clock time is higher than a parallel design.",
            "A single stall blocks all downstream stages.",
        ],
        "neutral": [
            "Stages can be skipped only when the plan has no files to implement.",
        ],
        "alternatives": [
            "Parallel agent fan-out (rejected: race conditions and context loss).",
            "Monolithic single agent (rejected: no stage-level verification).",
        ],
        "related": [
            ".claude/rules/01-pipeline-orchestration.md",
            "ADR-0010",
        ],
    },
    {
        "n": 2,
        "slug": "two-tier-model-routing",
        "title": "Two-Tier Model Routing (Opus 4.7 Critical, Sonnet 4.6 Standard)",
        "context": "Mixing models across stages controls cost while preserving quality where it matters.",
        "decision": "Route critical stages to claude-opus-4-7 and standard stages to claude-sonnet-4-6 via models.yaml.",
        "positive": [
            "Cost reduced on discovery, research, and pre-flight stages.",
            "Critical reasoning retained for plan, build, debug, review, decide.",
            "Single source of truth in models.yaml prevents drift.",
        ],
        "negative": [
            "Two-model setup increases test matrix size.",
            "Model version drift requires periodic yaml updates.",
        ],
        "neutral": [
            "Both tiers share the same tool surface and prompt format.",
        ],
        "alternatives": [
            "Opus everywhere (rejected: cost prohibitive for high-volume stages).",
            "Sonnet everywhere (rejected: quality regressions on planning).",
        ],
        "related": [
            "models.yaml",
            "ADR-0003",
        ],
    },
    {
        "n": 3,
        "slug": "confidence-based-model-escalation",
        "title": "Confidence-Based Model Escalation at Threshold 0.75",
        "context": "Standard-tier agents sometimes return low-confidence outputs that need stronger reasoning.",
        "decision": "Auto-promote any stage to tier_critical when the agent self-reports confidence below 0.75 or the stage is tagged critical.",
        "positive": [
            "Low-quality responses trigger automatic retry on a stronger model.",
            "Human intervention not required for routine escalations.",
            "Downgrade after three consecutive scores at or above 0.90 reduces cost.",
        ],
        "negative": [
            "Escalation can loop if the stronger model also underperforms.",
            "Self-reported confidence can be gamed without anti-cheating rules.",
        ],
        "neutral": [
            "Escalation state is logged for post-run analysis.",
        ],
        "alternatives": [
            "Manual escalation only (rejected: breaks autonomy rule).",
            "Always-on Opus for flagged stages (rejected: defeats two-tier cost model).",
        ],
        "related": [
            ".claude/rules/09-confidence-scoring.md",
            "ADR-0002",
        ],
    },
    {
        "n": 4,
        "slug": "em-dash-and-en-dash-ban",
        "title": "Em-Dash and En-Dash Ban Across All Outputs",
        "context": "Fancy dashes corrupt clipboards, produce noisy diffs, and break grep-based enforcement.",
        "decision": "Ban the four fancy dash code points in every file, message, comment, and commit; scan on every write.",
        "positive": [
            "Universal terminal and editor compatibility.",
            "Clean diffs without invisible punctuation churn.",
            "Simple grep and sed rules that work without Unicode flags.",
        ],
        "negative": [
            "Contributors lose a typographic option they may prefer.",
            "macOS smart-punctuation must be disabled on authoring tools.",
        ],
        "neutral": [
            "ASCII hyphen-minus, colon, comma, and period cover all replacement cases.",
        ],
        "alternatives": [
            "Allow fancy dashes in prose only (rejected: inconsistent across code and docs).",
            "Auto-rewrite in post-processing (rejected: still allows them upstream).",
        ],
        "related": [
            ".claude/rules/08-em-dash-ban.md",
            ".claude/hooks/pre_tool_use.py",
        ],
    },
    {
        "n": 5,
        "slug": "spacemail-insight-mcp-sole-email",
        "title": "Spacemail Insight MCP as Sole Email Transport",
        "context": "Direct provider SDKs fragment audit, suppression, and compliance logic across providers.",
        "decision": "Route every outbound message through mcp__claude_ai_Spacemail_Insight__* tools only.",
        "positive": [
            "Single audit trail for send, bounce, complaint, unsubscribe.",
            "Compliance footers and suppression list applied once, centrally.",
            "No SMTP or provider credentials held by application code.",
        ],
        "negative": [
            "Single point of failure requires queue absorption on outage.",
            "Feature parity depends on the MCP surface roadmap.",
        ],
        "neutral": [
            "Local queue drains through the MCP surface when service recovers.",
        ],
        "alternatives": [
            "Provider fallback on outage (rejected: voids audit and compliance).",
            "Per-service SDKs (rejected: audit trail fragmentation).",
        ],
        "related": [
            ".claude/rules/13-spacemail-only.md",
            "ADR-0025",
        ],
    },
    {
        "n": 6,
        "slug": "rls-enabled-on-every-table",
        "title": "RLS Enabled on Every Supabase Table",
        "context": "Supabase exposes every table through PostgREST, so missing RLS equals public data.",
        "decision": "Every CREATE TABLE in migrations must be followed by ENABLE ROW LEVEL SECURITY with explicit per-operation policies.",
        "positive": [
            "Authorization enforced in the database engine, not the app layer.",
            "Multi-tenant isolation survives application-layer bugs.",
            "Policies are auditable via pg_policies at any time.",
        ],
        "negative": [
            "Every new table adds at least four policy statements.",
            "Service-role backfills require careful scoping.",
        ],
        "neutral": [
            "FORCE ROW LEVEL SECURITY is required when the owner is also a tenant.",
        ],
        "alternatives": [
            "App-layer authorization only (rejected: framework CVEs bypass it).",
            "RLS on a subset of tables (rejected: inevitable oversight).",
        ],
        "related": [
            ".claude/rules/10-rls.md",
            "ADR-0007",
        ],
    },
    {
        "n": 7,
        "slug": "security-invoker-on-every-view",
        "title": "security_invoker Enabled on Every Supabase View",
        "context": "Views default to definer semantics so the owner bypasses RLS on underlying tables.",
        "decision": "Every CREATE VIEW and CREATE OR REPLACE VIEW must include WITH (security_invoker = on).",
        "positive": [
            "Views inherit the caller JWT and RLS policies automatically.",
            "Eliminates a common Supabase authorization bypass.",
            "Auditable via pg_class.reloptions across the schema.",
        ],
        "negative": [
            "Requires Postgres 15 or later for full support.",
            "Materialized views need a wrapper invoker view for tenant filtering.",
        ],
        "neutral": [
            "Functions default to SECURITY INVOKER with explicit annotation required.",
        ],
        "alternatives": [
            "Owner-restricted view grants (rejected: complex and easy to miss).",
            "Never use views on user data (rejected: loses ergonomics).",
        ],
        "related": [
            ".claude/rules/11-security-invoker.md",
            "ADR-0006",
        ],
    },
    {
        "n": 8,
        "slug": "keychain-age-encrypted-backup",
        "title": "macOS Keychain Plus age-Encrypted iCloud Backup for Secrets",
        "context": "Secrets in dotfiles, env files, and repos leak and cannot be rotated cleanly.",
        "decision": "Store runtime secrets in macOS Keychain; any off-device backup must be encrypted with age using a cold-stored identity.",
        "positive": [
            "Zero real credentials on disk in the working tree.",
            "iCloud backup is cryptographically protected end to end.",
            "Rotation has a documented 24-hour window and decision record.",
        ],
        "negative": [
            "Developers must run the with-secrets wrapper for every command.",
            "Windows and Linux require a different store (CI uses provider secrets).",
        ],
        "neutral": [
            "CI fallback uses GitHub, Vercel, Doppler, AWS, GCP, or Vault natively.",
        ],
        "alternatives": [
            "Dotenv files for dev (rejected: frequent leaks and no rotation).",
            "Single cloud vault for all secrets (rejected: online dependency).",
        ],
        "related": [
            ".claude/rules/12-keychain.md",
            "scripts/with-secrets.sh",
        ],
    },
    {
        "n": 9,
        "slug": "multi-critic-pr-gate-95-85",
        "title": "Multi-Critic PR Gate at Score 95 Production, 85 Hackathon",
        "context": "Code review quality varies across reviewers and time, and a numeric gate aligns expectations.",
        "decision": "Every PR must pass a multi-critic gate at 95 in production mode and 85 in hackathon mode, covering architecture, style, completeness, consistency.",
        "positive": [
            "Explicit quality bar that cannot be tacitly lowered.",
            "Hackathon mode permits velocity without removing the gate.",
            "Four-dimension scoring surfaces specific gaps rather than vague concerns.",
        ],
        "negative": [
            "Gate failure can block urgent fixes until re-critiqued.",
            "Score inflation must be actively prevented by anti-cheating rules.",
        ],
        "neutral": [
            "Rubric is shared with agents via .claude/rules/09-confidence-scoring.md.",
        ],
        "alternatives": [
            "Single reviewer approval (rejected: variance too high).",
            "No numeric gate (rejected: relies on memory of standards).",
        ],
        "related": [
            ".claude/rules/09-confidence-scoring.md",
            "ADR-0011",
        ],
    },
    {
        "n": 10,
        "slug": "decision-records-per-stage",
        "title": "Decision Records to docs/decisions/YYYY-MM-DD.md per Stage",
        "context": "Stages make non-trivial choices that need durable context for future debugging.",
        "decision": "Every stage with a non-trivial decision writes an entry to docs/decisions/YYYY-MM-DD.md with rationale, alternatives, and confidence.",
        "positive": [
            "Long-term memory of why a choice was made survives personnel changes.",
            "Rollback plans become concrete rather than implicit.",
            "Cross-links from commits and PRs to records are simple.",
        ],
        "negative": [
            "Extra writing overhead per stage.",
            "Records can drift from current state if not updated on reversal.",
        ],
        "neutral": [
            "Templates reduce the time cost of writing a record.",
        ],
        "alternatives": [
            "Commit messages as the only record (rejected: too terse).",
            "Wiki pages (rejected: leaves the repo and loses review).",
        ],
        "related": [
            "docs/decisions",
            "ADR-0001",
        ],
    },
    {
        "n": 11,
        "slug": "confidence-score-on-every-completion",
        "title": "Confidence Score 0 to 100 Appended to Every Completion",
        "context": "Without a numeric self-assessment the orchestrator cannot gate or escalate automatically.",
        "decision": "Every agent completion ends with a CONFIDENCE block scoring four dimensions summing to 0 to 100 with a justification.",
        "positive": [
            "Automatic rerun below 90 without human review.",
            "Rolling average across a pipeline exposes systemic quality issues.",
            "Score supports model escalation decisions per ADR-0003.",
        ],
        "negative": [
            "Score inflation is possible without strict anti-cheating rules.",
            "Every agent output grows by a small fixed block.",
        ],
        "neutral": [
            "Block format is defined in rule 09, not in orchestrator rules.",
        ],
        "alternatives": [
            "Human rubric review (rejected: breaks autonomy).",
            "Pass/fail only (rejected: loses signal needed for escalation).",
        ],
        "related": [
            ".claude/rules/09-confidence-scoring.md",
            "ADR-0003",
        ],
    },
    {
        "n": 12,
        "slug": "full-autonomy-bypass-permissions",
        "title": "Full Autonomy via bypassPermissions, Blockers Parked in open-items.md",
        "context": "Interactive prompts during long pipelines halt progress and erode throughput.",
        "decision": "Run in bypassPermissions mode and never ask the user; when blocked, log to docs/open-items.md and continue.",
        "positive": [
            "End-to-end runs complete without human intervention.",
            "Blockers are explicit, centralized, and tractable.",
            "Safety rails are preserved through hooks, not prompts.",
        ],
        "negative": [
            "A malformed plan can do more harm before detection.",
            "Requires strong pre-write hooks for security and correctness.",
        ],
        "neutral": [
            "User confirmation still happens once after task-breakdown.",
        ],
        "alternatives": [
            "Prompted approval at every destructive step (rejected: velocity loss).",
            "Full dry-run mode (rejected: forks execution semantics).",
        ],
        "related": [
            "docs/open-items.md",
            "CLAUDE.md",
        ],
    },
    {
        "n": 13,
        "slug": "launchd-keepalive-throttle",
        "title": "launchd KeepAlive true and ThrottleInterval 30 for Long-Running Work",
        "context": "Long workers die from resource pressure and need automatic recovery without tight restart loops.",
        "decision": "Register long-running jobs under macOS launchd with KeepAlive true and ThrottleInterval 30 seconds.",
        "positive": [
            "Crashed workers restart automatically.",
            "Throttle prevents CPU spin during repeated early failures.",
            "launchd logs provide a consistent failure view.",
        ],
        "negative": [
            "macOS-only; linux targets need systemd equivalents.",
            "ThrottleInterval delays recovery from transient errors.",
        ],
        "neutral": [
            "plists live in ~/Library/LaunchAgents with version control stubs.",
        ],
        "alternatives": [
            "nohup and shell loops (rejected: no crash telemetry).",
            "pm2 (rejected: extra dependency for minimal gain on macOS).",
        ],
        "related": [
            "docs/runbooks/release.md",
            "ADR-0014",
        ],
    },
    {
        "n": 14,
        "slug": "fsnotify-file-watcher",
        "title": "File Watcher via fsnotify with 250ms Debounce and 30s Poll Fallback",
        "context": "File events must arrive quickly without flooding handlers, and some filesystems drop events.",
        "decision": "Use fsnotify with a 250ms debounce window and a 30-second polling fallback for dropped events.",
        "positive": [
            "Low latency on healthy filesystems via native events.",
            "Debounce absorbs editor save bursts without handler thrash.",
            "Polling fallback catches missed events on NFS and iCloud paths.",
        ],
        "negative": [
            "Poll adds a steady low-rate IO load.",
            "Debounce window delays the fastest legitimate update.",
        ],
        "neutral": [
            "Both values are configurable per deployment.",
        ],
        "alternatives": [
            "Pure polling (rejected: poor latency at busy hours).",
            "No debounce (rejected: handler amplification).",
        ],
        "related": [
            "ADR-0013",
            "scripts/sync-framework-to-work-tree.sh",
        ],
    },
    {
        "n": 15,
        "slug": "memory-lancedb-hybrid",
        "title": "Memory System on Embedded LanceDB with Hybrid BM25 Plus Dense Rerank",
        "context": "Agent memory needs fast similarity over large corpora without a managed vector service.",
        "decision": "Use embedded LanceDB with BM25 for lexical recall and a dense reranker for precision on top results.",
        "positive": [
            "Local file store with no network dependency.",
            "Hybrid retrieval outperforms either BM25 or dense alone.",
            "Rerank applied only to the top K keeps latency low.",
        ],
        "negative": [
            "Single-process access pattern limits concurrency.",
            "LanceDB version upgrades require data-file rewrites.",
        ],
        "neutral": [
            "Can be swapped for pgvector later without API changes.",
        ],
        "alternatives": [
            "pgvector only (rejected: weaker lexical performance).",
            "Pinecone or Weaviate (rejected: external dependency).",
        ],
        "related": [
            "ADR-0016",
            "ADR-0017",
        ],
    },
    {
        "n": 16,
        "slug": "qwen3-jina-embedders",
        "title": "Qwen3 General and Jina Code Embedders with Jina Tiny Reranker",
        "context": "Different content types benefit from different embedders, and rerank cost must stay bounded.",
        "decision": "Embed general text with Qwen3, code with Jina code embedder, and rerank with Jina tiny reranker.",
        "positive": [
            "Domain-specific embedders improve retrieval on code spans.",
            "Tiny reranker fits the local latency budget.",
            "Model choices are independently upgradable.",
        ],
        "negative": [
            "Two embedder pipelines double model-hosting surface.",
            "Mixed embeddings require careful index partitioning.",
        ],
        "neutral": [
            "Indexes are versioned so a migration can run offline.",
        ],
        "alternatives": [
            "OpenAI embeddings (rejected: network dependency and cost).",
            "Single general embedder (rejected: weaker on code spans).",
        ],
        "related": [
            "ADR-0015",
            "ADR-0018",
        ],
    },
    {
        "n": 17,
        "slug": "three-stage-dedup",
        "title": "Three-Stage Dedup (SimHash, MinHash LSH, Semantic Cosine with NLI)",
        "context": "Agent logs and diffs contain many near-duplicates that inflate cost and dilute retrieval.",
        "decision": "Deduplicate in three stages: SimHash for near-exact, MinHash LSH for approximate, then semantic cosine with NLI for paraphrase.",
        "positive": [
            "Each stage removes a different class of duplicate at minimal cost.",
            "NLI catches semantic paraphrase that hashes miss.",
            "Pipeline order keeps expensive steps on a small residual.",
        ],
        "negative": [
            "NLI model hosting adds a runtime dependency.",
            "False positives on borderline semantic matches need tuning.",
        ],
        "neutral": [
            "Thresholds are per-corpus tunable.",
        ],
        "alternatives": [
            "SimHash only (rejected: misses paraphrase).",
            "NLI on all pairs (rejected: quadratic cost).",
        ],
        "related": [
            "ADR-0015",
            "ADR-0018",
        ],
    },
    {
        "n": 18,
        "slug": "memory-ttl-tiers",
        "title": "Memory TTL Tiers (7d Logs, 30d Traces, 60d Diffs, 180d Lessons)",
        "context": "Storing everything forever bloats the index and reduces retrieval quality.",
        "decision": "Apply tiered TTLs: 7 days for raw logs, 30 days for traces, 60 days for diffs, 180 days for distilled lessons.",
        "positive": [
            "Index size stays bounded over time.",
            "High-value lessons persist longer than raw events.",
            "Purge cadence aligns with debugging recency needs.",
        ],
        "negative": [
            "Incident forensics older than 7 days lack raw log detail.",
            "TTL tuning may require adjustment for specific projects.",
        ],
        "neutral": [
            "Lessons are distilled by a summarization job before lower tiers expire.",
        ],
        "alternatives": [
            "Uniform 90-day TTL (rejected: either loses lessons or keeps noise).",
            "Infinite retention (rejected: degrades retrieval precision).",
        ],
        "related": [
            "ADR-0015",
            "ADR-0017",
        ],
    },
    {
        "n": 19,
        "slug": "publishing-play-api-v3-chrome",
        "title": "Publishing Pipeline Splits Play API v3 and Chrome Automator",
        "context": "Play Console API covers most release actions but some flows require a live browser.",
        "decision": "Use Play Developer API v3 for programmable actions and a Chrome automator for flows that still require console interaction.",
        "positive": [
            "Programmable release for uploads, tracks, and rollout percentages.",
            "Browser automation covers closed testing setup and some policy flows.",
            "Each path has its own retry and logging contract.",
        ],
        "negative": [
            "Two code paths to maintain.",
            "Browser automation is fragile to console UI changes.",
        ],
        "neutral": [
            "Automator runs under claude-in-chrome MCP tools where possible.",
        ],
        "alternatives": [
            "API-only (rejected: cannot complete all current flows).",
            "Browser-only (rejected: slow and flaky for programmable actions).",
        ],
        "related": [
            "publishing",
            "ADR-0020",
        ],
    },
    {
        "n": 20,
        "slug": "closed-testing-12-testers-14-days",
        "title": "Closed Testing Requirement 12 Testers over 14 Consecutive Days",
        "context": "Google requires personal developer accounts to complete a closed test with 12 testers for 14 days before production.",
        "decision": "Every new Play release from a personal account must complete closed testing with at least 12 active testers for 14 consecutive days.",
        "positive": [
            "Matches Google policy exactly, avoiding rejection at promotion.",
            "Tester tracking is automated via invite and audit queries.",
            "Release calendar reflects the real fastest path to production.",
        ],
        "negative": [
            "Adds a minimum two-week delay to first production release.",
            "Tester churn can reset eligibility.",
        ],
        "neutral": [
            "Business-account publications are exempt and tracked separately.",
        ],
        "alternatives": [
            "Skip closed testing (rejected: Google policy violation).",
            "Internal testing only (rejected: insufficient for production eligibility).",
        ],
        "related": [
            "docs/runbooks/release.md",
            "ADR-0019",
        ],
    },
    {
        "n": 21,
        "slug": "android-api-35-16kb-billing-v8",
        "title": "Android API 35 Target Plus 16 KB Memory Pages Plus Play Billing v8.3.0",
        "context": "Google requires API 35 targeting, 16 KB memory page support, and a current Play Billing library for new and updated releases.",
        "decision": "Target Android API 35, enable 16 KB memory page alignment, and ship with Play Billing Library v8.3.0.",
        "positive": [
            "Eligible for Play production and update windows.",
            "Forward compatible with upcoming device memory layouts.",
            "Newer billing API exposes current purchase and subscription flows.",
        ],
        "negative": [
            "Older build tooling needs upgrade across every module.",
            "Some native libraries lack 16 KB-aligned releases and need substitution.",
        ],
        "neutral": [
            "CI asserts these values on every build via Gradle checks.",
        ],
        "alternatives": [
            "API 34 target (rejected: future Play blocks at policy deadline).",
            "Older Billing client (rejected: loses required purchase signals).",
        ],
        "related": [
            "ADR-0023",
            "ADR-0024",
        ],
    },
    {
        "n": 22,
        "slug": "screenshot-real-ui-claude-frames",
        "title": "Screenshot Pipeline Uses Real UI Captures Inside Claude-Generated Frames",
        "context": "Store screenshots must reflect the real app, but surrounding frames benefit from polished image generation.",
        "decision": "Capture real UI from the running app and composite it into Claude-generated device frames and marketing backgrounds.",
        "positive": [
            "Screenshots never misrepresent actual app behavior.",
            "Marketing frames look consistent and polished.",
            "Per-locale screenshots scale via templated frames.",
        ],
        "negative": [
            "Two-step pipeline is slower than pure capture.",
            "Frame updates require regenerating assets.",
        ],
        "neutral": [
            "Claude image generation is used only outside the device screen area.",
        ],
        "alternatives": [
            "Fully generated screenshots (rejected: misrepresents the app).",
            "Plain captures only (rejected: weaker on store conversion).",
        ],
        "related": [
            "screenshots",
            "CLAUDE.md",
        ],
    },
    {
        "n": 23,
        "slug": "shorebird-code-push-in-app-update",
        "title": "Shorebird Code Push Plus in_app_update for App Update Flow",
        "context": "Flutter releases benefit from fast patch delivery for Dart code while native updates still go through the store.",
        "decision": "Use Shorebird for Dart code pushes and in_app_update for native Play-based app updates.",
        "positive": [
            "Dart-level bug fixes ship within minutes.",
            "Native updates follow store policy and review.",
            "User-facing update UI remains consistent via in_app_update.",
        ],
        "negative": [
            "Two update channels complicate release notes.",
            "Shorebird patches constrain certain native-dependent features.",
        ],
        "neutral": [
            "Rollback semantics differ between channels and are documented.",
        ],
        "alternatives": [
            "Store-only updates (rejected: slow bug fix turnaround).",
            "Custom OTA (rejected: reinvents Shorebird at higher risk).",
        ],
        "related": [
            "ADR-0021",
            "docs/runbooks/rollback.md",
        ],
    },
    {
        "n": 24,
        "slug": "revenuecat-subscriptions",
        "title": "RevenueCat as Subscription Source of Truth, Play Developer Notifications",
        "context": "Subscription state across platforms and store receipts must reconcile in one place.",
        "decision": "Use RevenueCat as the subscription source of truth and subscribe to Play Developer Notifications for event-driven updates.",
        "positive": [
            "Unified entitlement model across Android and iOS.",
            "Webhook-driven updates replace expensive polling.",
            "Dashboards show churn, MRR, and refunds in one view.",
        ],
        "negative": [
            "External dependency with its own outage modes.",
            "Per-active-user pricing grows with scale.",
        ],
        "neutral": [
            "Can be replaced by a direct integration later without schema churn.",
        ],
        "alternatives": [
            "Direct store APIs (rejected: heavy reconciliation burden).",
            "Custom receipt validator (rejected: long-tail edge cases).",
        ],
        "related": [
            "ADR-0021",
            "ADR-0027",
        ],
    },
    {
        "n": 25,
        "slug": "fly-r2-supabase-stack",
        "title": "Fly.io for Long Workers, Cloudflare R2 for Blobs, Supabase for OLTP",
        "context": "Different workload shapes need different hosts and object stores.",
        "decision": "Run long workers on Fly.io, store blobs on Cloudflare R2, and keep OLTP on Supabase Postgres.",
        "positive": [
            "Each tier hosted on the right primitive for its shape.",
            "R2 egress pricing is favorable versus alternatives.",
            "Supabase provides RLS, auth, and Postgres in one surface.",
        ],
        "negative": [
            "Three-vendor stack requires matching IAM and secret rotation flows.",
            "Cross-cloud latency must be measured on the critical path.",
        ],
        "neutral": [
            "Observability is federated via OpenTelemetry.",
        ],
        "alternatives": [
            "All-AWS stack (rejected: higher egress, weaker Supabase ergonomics).",
            "Single-region single-vendor (rejected: vendor lock-in risk).",
        ],
        "related": [
            "ADR-0026",
            "ADR-0028",
        ],
    },
    {
        "n": 26,
        "slug": "cloudflare-pages-workers-nextjs",
        "title": "Cloudflare Pages Plus Workers for Next.js Web Hosting",
        "context": "The web app needs edge rendering, low cold-start times, and tight integration with R2 and KV.",
        "decision": "Host the Next.js web app on Cloudflare Pages with Workers for server-side features and bindings to R2 and KV.",
        "positive": [
            "Edge execution keeps latency low globally.",
            "Native R2 and KV bindings avoid cross-cloud hops.",
            "Pages deploy pipeline integrates with GitHub out of the box.",
        ],
        "negative": [
            "Workers runtime has specific Node-compat limitations.",
            "Some Next.js features require Pages-specific adapters.",
        ],
        "neutral": [
            "Preview environments are automatic per branch.",
        ],
        "alternatives": [
            "Vercel (rejected: weaker R2 integration and egress).",
            "Self-hosted Next.js on Fly (rejected: cold-start and global distribution).",
        ],
        "related": [
            "ADR-0025",
            "ADR-0028",
        ],
    },
    {
        "n": 27,
        "slug": "fcm-supabase-push",
        "title": "Firebase Cloud Messaging Plus Supabase Trigger for Push Notifications",
        "context": "Push delivery needs a reliable transport plus a programmable trigger bound to data changes.",
        "decision": "Use Firebase Cloud Messaging for delivery and a Supabase database trigger to enqueue pushes from row changes.",
        "positive": [
            "FCM handles device registration, delivery, and QoS on both platforms.",
            "Supabase trigger keeps push logic close to the data model.",
            "No extra worker tier needed for most flows.",
        ],
        "negative": [
            "FCM quota limits must be managed for large fan-out.",
            "Trigger code runs in Postgres and must be kept small.",
        ],
        "neutral": [
            "Fan-out heavy flows can be redirected to a Fly worker (ADR-0025).",
        ],
        "alternatives": [
            "OneSignal (rejected: added vendor overlap).",
            "Custom push gateway (rejected: device token lifecycle complexity).",
        ],
        "related": [
            "ADR-0024",
            "ADR-0025",
        ],
    },
    {
        "n": 28,
        "slug": "posthog-eu-analytics",
        "title": "PostHog Cloud EU with Autocapture Off as Analytics Platform",
        "context": "Analytics must meet EU data-residency expectations and avoid accidental PII capture.",
        "decision": "Use PostHog Cloud EU with autocapture disabled and explicit event-schema definitions.",
        "positive": [
            "EU residency aligns with GDPR expectations for EU users.",
            "Disabled autocapture prevents inadvertent PII ingestion.",
            "Explicit schemas keep dashboards stable over time.",
        ],
        "negative": [
            "Manual event definition slows initial instrumentation.",
            "EU-only region limits some PostHog beta features.",
        ],
        "neutral": [
            "Event taxonomy is versioned alongside the app.",
        ],
        "alternatives": [
            "Autocapture on (rejected: PII leakage risk).",
            "Self-hosted PostHog (rejected: operational overhead).",
        ],
        "related": [
            "ADR-0025",
            "ADR-0012",
        ],
    },
    {
        "n": 29,
        "slug": "agent-skill-semver-frontmatter",
        "title": "Agent and Skill Semver Frontmatter with Load-Time Version Check",
        "context": "Agents and skills evolve and callers need to detect incompatible versions at load time.",
        "decision": "Each agent and skill declares a semver in frontmatter and the loader enforces compatibility against declared requirements.",
        "positive": [
            "Incompatible changes surface immediately at load.",
            "Callers can pin exact or compatible versions.",
            "Upgrades have a documented deprecation path.",
        ],
        "negative": [
            "Every edit must consider version impact.",
            "Loader must be kept in sync with semver rules.",
        ],
        "neutral": [
            "CI asserts version fields exist and parse.",
        ],
        "alternatives": [
            "No versioning (rejected: silent breaking changes).",
            "Date-based versions (rejected: weaker compatibility semantics).",
        ],
        "related": [
            "scripts/check_agent_versions.py",
            "scripts/upgrade_agents_skills.py",
        ],
    },
    {
        "n": 30,
        "slug": "bootstrap-script-provisions-all",
        "title": "Project Bootstrap Script Creates Repo Plus Supabase Plus Cloudflare Plus GitHub Plus Keychain",
        "context": "New projects need repeatable provisioning of every dependency before the first commit.",
        "decision": "A single bootstrap script creates the GitHub repo, Supabase project, Cloudflare assets, Keychain items, and seed files in one run.",
        "positive": [
            "One command produces a running skeleton.",
            "Every artifact is named by policy, not by accident.",
            "Secret items land in Keychain rather than env files.",
        ],
        "negative": [
            "Bootstrap script must track provider API changes.",
            "Partial failures need idempotent retry logic.",
        ],
        "neutral": [
            "Script is covered by a runbook for manual recovery.",
        ],
        "alternatives": [
            "Manual provisioning (rejected: inconsistent per project).",
            "Terraform only (rejected: does not cover Keychain or GitHub repo init).",
        ],
        "related": [
            "ADR-0008",
            "ADR-0025",
        ],
    },
]


def adr_to_markdown(adr: dict) -> str:
    num = f"{adr['n']:04d}"
    lines = []
    lines.append(f"# ADR-{num}: {adr['title']}")
    lines.append("")
    lines.append("## Status")
    lines.append("accepted")
    lines.append("")
    lines.append("## Context")
    lines.append(adr["context"])
    lines.append("")
    lines.append("## Decision")
    lines.append(adr["decision"])
    lines.append("")
    lines.append("## Consequences")
    lines.append("")
    lines.append("### Positive")
    for b in adr["positive"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("### Negative")
    for b in adr["negative"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("### Neutral")
    for b in adr["neutral"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Alternatives Considered")
    for b in adr["alternatives"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Related")
    for b in adr["related"]:
        lines.append(f"- {b}")
    lines.append("")
    return "\n".join(lines)


RUNBOOKS = [
    {
        "slug": "crash-to-fix",
        "title": "Sentry Crash to Merged Fix in 10 Minutes",
        "purpose": "Turn a fresh Sentry issue into a merged PR within 10 minutes via the debugger agent pipeline.",
        "prereqs": [
            "Sentry project configured with release tag on the crashed build.",
            "Local Keychain entry for SENTRY_AUTH_TOKEN and GH_TOKEN.",
            "Shorebird and Play credentials loaded via scripts/with-secrets.sh.",
            "Repository clean on main with no unrelated uncommitted changes.",
        ],
        "procedure": [
            "Open the top Sentry issue and copy its short id and stack trace.",
            "Run scripts/with-secrets.sh claude 'fix sentry issue <id>' to start the pipeline.",
            "pipeline-scaler routes the task to a single run with critical flags.",
            "code-discovery maps the affected files from the stack trace.",
            "plan-agent creates a 1 to 2 file patch with test batches.",
            "build-agent implements the fix and test-writer adds regression tests.",
            "debugger runs the tests and fixes any residual errors.",
            "review-agent checks the patch against acceptance criteria from the TaskSpec.",
            "decide-agent outputs COMPLETE and opens a PR via gh pr create.",
        ],
        "verification": [
            "Sentry issue moves to resolved on next release after auto-assignment.",
            "CI run on the PR passes lint, unit, and integration suites.",
            "Coverage delta on the patch is at or above 0.85 for changed lines.",
            "review-agent confidence is at or above 95.",
        ],
        "rollback": [
            "Close the PR if the diagnosis was incorrect.",
            "Revert the merge commit with git revert <sha> if already merged.",
            "Open a new Sentry issue reference in docs/open-items.md.",
            "Notify the release channel that the rollback was published.",
        ],
        "escalation": [
            "Primary: on-call engineer via PagerDuty.",
            "Secondary: release captain for the affected module.",
            "Tertiary: security lead if the crash touches auth or payments.",
        ],
        "related": [
            "ADR-0001",
            "ADR-0011",
        ],
    },
    {
        "slug": "restore-drill",
        "title": "Supabase PITR Restore Drill",
        "purpose": "Exercise point-in-time recovery on Supabase with a 14-day retention window and a four-hour recovery time objective.",
        "prereqs": [
            "Supabase project with PITR enabled on the Pro plan or higher.",
            "Service-role key stored in Keychain under com.example.myapp.supabase_service_role.",
            "Staging Supabase project reserved for restore targets.",
            "psql client installed locally.",
        ],
        "procedure": [
            "Select a target recovery point no older than 14 days.",
            "Open the Supabase dashboard, navigate to Database then Backups then PITR.",
            "Click Restore and pick the target timestamp to the second.",
            "Choose the staging project as the restore target, not production.",
            "Wait for the restore to finish; observe the status badge until Ready.",
            "Connect to the staging project with psql and run the row-count queries.",
            "Compare row counts against production baseline queries from the same timestamp.",
            "Record any drift in docs/decisions under a restore-drill record.",
        ],
        "verification": [
            "Row count per top-level table differs by no more than five rows versus baseline.",
            "Restored DB exposes the expected RLS policies on every user table.",
            "Views in the restored DB have security_invoker set on every entry.",
            "Total elapsed time from click to verified restore is under four hours.",
        ],
        "rollback": [
            "Do not promote the restore target to production.",
            "Shut the staging project once the drill is complete to control cost.",
            "Purge any PII copied into the staging project according to retention policy.",
            "Update the drill record with failures, timings, and lessons learned.",
        ],
        "escalation": [
            "Primary: database owner.",
            "Secondary: infrastructure lead.",
            "Tertiary: Supabase support for PITR-specific issues.",
        ],
        "related": [
            "ADR-0006",
            "ADR-0025",
        ],
    },
    {
        "slug": "release",
        "title": "Build, Critic, and Promote Android Release",
        "purpose": "Produce a signed AAB, pass the critic gate at 95, and promote the build across Play tracks.",
        "prereqs": [
            "Keychain entries for signing key alias and keystore password.",
            "Play Console access with the release manager role on the target app.",
            "Closed testing tester list with at least 12 active testers (ADR-0020).",
            "Local flutter and android build toolchains at the pinned versions.",
        ],
        "procedure": [
            "Check out the release branch and confirm the pinned versions with scripts/check_agent_versions.py.",
            "Run scripts/with-secrets.sh flutter build appbundle --release --obfuscate --split-debug-info=./debug-info/.",
            "Run the critic gate via the multi-critic agent; require a score of 95 or higher.",
            "Upload the AAB to the internal track via the Play Developer API v3.",
            "Promote from internal to closed after smoke testing on two physical devices.",
            "Collect closed testing feedback over the required 14 consecutive days.",
            "Promote from closed to production with a staged rollout at 10 percent.",
            "Ramp the rollout to 100 percent over 72 hours unless a halt signal fires.",
        ],
        "verification": [
            "Critic gate score is 95 or higher with all four dimensions at 20 or higher.",
            "Play Console shows the build on the target track with the expected version name.",
            "Crash-free user rate is at or above 0.995 during the staged rollout window.",
            "Subscription flows work on a physical device using Play Billing v8.",
        ],
        "rollback": [
            "Halt the rollout from the Play Console if crash-free rate drops below 0.99.",
            "Follow docs/runbooks/rollback.md to publish the previous good version.",
            "Open an incident record in docs/decisions with root cause and mitigation.",
            "Disable Shorebird patches that may have caused the regression (ADR-0023).",
        ],
        "escalation": [
            "Primary: release captain.",
            "Secondary: Android platform owner.",
            "Tertiary: Google Play support via the priority queue.",
        ],
        "related": [
            "ADR-0019",
            "ADR-0021",
        ],
    },
    {
        "slug": "rollback",
        "title": "Play Track Rollback via Halt and Previous Release",
        "purpose": "Roll back a Play track to the previous known-good version by halting the current rollout and republishing the prior AAB.",
        "prereqs": [
            "Play Console access with the release manager role.",
            "Previous AAB archived in Cloudflare R2 under the release bucket.",
            "Keychain entries for signing key alias and keystore password.",
            "On-call engineer paged and aware the rollback is in progress.",
        ],
        "procedure": [
            "Open the Play Console and navigate to the affected track.",
            "Click Halt rollout on the current release to stop further delivery.",
            "Create a new release on the same track using the previous AAB from R2.",
            "Set the release notes to reference the rollback and the original issue id.",
            "Submit the release with staged rollout at 10 percent.",
            "Monitor crash-free user rate for 30 minutes before ramping further.",
            "Ramp to 50 percent, then to 100 percent once the crash-free rate stabilizes.",
            "Record the rollback in docs/decisions with the halt timestamp and rollback AAB version.",
        ],
        "verification": [
            "Halt takes effect within five minutes of click (Play Console status).",
            "Crash-free user rate returns to pre-incident levels within 60 minutes.",
            "Previous AAB is the only active build on the target track.",
            "Sentry releases dashboard reflects the rollback version as current.",
        ],
        "rollback": [
            "If the rollback itself regresses, halt the rollback release.",
            "Contact Google Play support via the priority queue for emergency pull.",
            "Disable Shorebird patches that may be masking or worsening the issue.",
            "Update docs/open-items.md with the active incident status.",
        ],
        "escalation": [
            "Primary: release captain.",
            "Secondary: incident commander from PagerDuty rotation.",
            "Tertiary: executive sponsor if user-visible impact exceeds four hours.",
        ],
        "related": [
            "ADR-0019",
            "ADR-0023",
        ],
    },
]


def runbook_to_markdown(rb: dict) -> str:
    lines = []
    lines.append(f"# Runbook: {rb['title']}")
    lines.append("")
    lines.append("## Purpose")
    lines.append(rb["purpose"])
    lines.append("")
    lines.append("## Prerequisites")
    for b in rb["prereqs"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Procedure")
    for i, step in enumerate(rb["procedure"], start=1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("## Verification")
    for b in rb["verification"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Rollback")
    for i, step in enumerate(rb["rollback"], start=1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("## Escalation")
    for b in rb["escalation"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Related ADRs")
    for b in rb["related"]:
        lines.append(f"- {b}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    decisions_dir = repo_root / "docs" / "decisions"
    runbooks_dir = repo_root / "docs" / "runbooks"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    runbooks_dir.mkdir(parents=True, exist_ok=True)

    total_lines = 0
    adr_count = 0
    for adr in ADRS:
        num = f"{adr['n']:04d}"
        filename = f"{num}-{adr['slug']}.md"
        body = adr_to_markdown(adr)
        scan(body, filename)
        path = decisions_dir / filename
        path.write_text(body, encoding="utf-8")
        total_lines += body.count("\n") + 1
        adr_count += 1

    runbook_count = 0
    for rb in RUNBOOKS:
        filename = f"{rb['slug']}.md"
        body = runbook_to_markdown(rb)
        scan(body, filename)
        path = runbooks_dir / filename
        path.write_text(body, encoding="utf-8")
        total_lines += body.count("\n") + 1
        runbook_count += 1

    print("ADRs created:", adr_count)
    print("Runbooks created:", runbook_count)
    print("Total markdown lines:", total_lines)
    print("Dash scan: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
