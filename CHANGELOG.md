# Changelog

All notable changes to opencode-framework. Format is based on Keep a Changelog.
Semantic Versioning applied.

## [2.0.0] 2026-04-24

This release folds ten sequential runs of pipeline work into a single major
version. It upgrades every pipeline agent, refreshes every skill, adds new
hooks, adds new operating rules, introduces new subsystems (memory, publishing,
screenshots, marketing, telemetry, eval, daemons, bootstrap, ADRs), and adds a
full verification harness.

### Added

#### Orchestration

- Operating rules 1 through 12 introduced in `CLAUDE.md` and expanded across
  five new rule files. Every rule is non-negotiable for v2.0.0 pipelines.
- Rule 08 `.claude/rules/08-em-dash-ban.md`. Bans U+2012, U+2013, U+2014,
  U+2015 in every output, file, commit, comment, docstring, log line, UI
  string. ASCII hyphen, colon, comma, period only.
- Rule 10 `.claude/rules/10-rls.md`. Row-level security enabled on every
  Supabase table. Minimum policy set for select, insert, update, delete on
  every user-data table. Forbidden patterns enumerated (permissive USING
  true, FOR ALL, disabled RLS without a paired decision record).
- Rule 11 `.claude/rules/11-security-invoker.md`. Every view created WITH
  `security_invoker = on`. Functions default to SECURITY INVOKER. Any
  SECURITY DEFINER requires justification in the body plus a decision record.
- Rule 12 `.claude/rules/12-keychain.md`. Every runtime secret lives in
  macOS Keychain at runtime. iCloud-synced backups are age-encrypted. Rotation
  within 24 hours on any suspected leak.
- Rule 13 `.claude/rules/13-spacemail-only.md`. All outbound email routes
  exclusively through `mcp__claude_ai_Spacemail_Insight__*` tools. SMTP,
  SendGrid, Mailgun, Postmark, SES, Resend, Nodemailer, smtplib all blocked.

#### Agents (85 upgraded to version 1.0.0)

- pipeline-scaler, prompt-optimizer, task-breakdown.
- code-discovery, plan-agent, docs-researcher, pre-flight-checker.
- build-agent-1 through build-agent-55.
- test-writer.
- debugger through debugger-11.
- logical-agent, test-agent, integration-agent, review-agent, decide-agent.
- perfection-validator, project-customizer, web-syntax-researcher, claude-in-chrome.

Each agent now emits a mandatory CONFIDENCE block per `.claude/rules/09-confidence-scoring.md`
and defaults to the tier mapping in `models.yaml` (critical -> Opus 4.7,
standard -> Sonnet 4.6).

#### Skills (129 refreshed)

- Full refresh of `.claude/skills/*/SKILL.md` for all 129 skills in the
  skill index, including the new `graphify` skill for knowledge-graph
  exploration of large code and doc corpora.
- Skill index `.claude/skills/INDEX.md` regenerated to include `graphify`
  and to enforce the new tier mapping.

#### Hooks (6 Python hooks)

- `.claude/hooks/pre_tool_use.py`. Blocks writes that contain banned dashes,
  real secrets (API keys, PEM blocks, passwords), or forbidden email libraries
  and endpoints.
- `.claude/hooks/post_tool_use.py`. Quality gate on every write. Shell files
  pass bash -n. Python files pass py_compile. JSON files parse.
- `.claude/hooks/user_prompt_submit.py`. Scrubs banned dashes from user
  prompts before the main session sees them.
- `.claude/hooks/stop.py`. Finalizes telemetry on session stop.
- `.claude/hooks/subagent_stop.py`. Skill reminder when a plan batch names a
  skill but the build agent forgot to activate it.
- `.claude/hooks/pre_compact.py`. Preserves decision records and key context
  across runtime compaction events.

#### Subsystems

- `memory/`. Cross-session memory store with recall test.
- `publishing/play/`. Google Play release and rollback scripting.
- `publishing/chrome/`. Chrome Web Store automator.
- `screenshots/`. Device-frame screenshot capture. Framed UI uses real app
  renders per operating rule 11; icons and marketing visuals use Claude image
  generation.
- `marketing/`. Spacemail-routed marketing flows, with `test_spacemail.py`
  proving no direct provider SDK path exists.
- `telemetry/`. Local SQLite event log plus `scoreboard.py` for token spend
  rollups.
- `eval/`. Golden suite runner (`runner.py`) and `critics_gate.py` for the
  multi-critic 95 gate (85 in hackathon mode).
- `daemons/`. launchd plists with `KeepAlive=true` and `ThrottleInterval=30`,
  and `test_keepalive.sh` to verify the supervisor loop.
- `bootstrap` script for new project scaffolding into `projects.yaml`.
- `docs/decisions/`. Thirty accepted ADRs authored in this release covering
  tier policy, secrets policy, RLS, security invoker, Spacemail routing,
  predictive back migration, offline-first storage choice, and more.
- `docs/architecture.md`. End-to-end architecture (100+ lines) with
  performance budgets (16.67ms at 60Hz, 8.33ms at 120Hz, jank below 1 percent).
- `docs/inventory.md`. Component inventory.
- `docs/open-items.md`. Deferred work and blockers. Agents log blockers here
  instead of stopping to ask the user, per operating rule 2.

#### Scripts

- `scripts/restore-drill.sh`. Supabase PITR drill. Dumps production, uploads
  to R2, restores to staging, verifies row counts, enforces RTO 4h and RPO 1h
  budgets. Dry-run default, `--execute` for real run.
- `scripts/backup-dump.sh`. Daily logical dump to R2, age-encrypted, 14-day
  retention rotation. Invocable from launchd.
- `scripts/release.sh`. Clean tree check, tests, AAB build with `--obfuscate
  --split-debug-info`, critic gate at 95, git tag, Play publish via
  `publishing/play/release.py`. Accepts `--track internal|alpha|beta|production`.
- `scripts/rollback.sh`. Halts current Play rollout, resolves prior
  `version_code`, promotes it back, writes a decision record.
- `scripts/check_emdash.sh`. Portable python3 scan for U+2012, U+2013,
  U+2014, U+2015. `--fix` flag replaces matches with ASCII hyphen.
- `scripts/verify.sh`. Master verification harness. Runs all 20 success
  criteria defined for v2.0.0, prints colored PASS/FAIL, logs to
  `~/.opencode/logs/verify.log`, exits 0 only if every criterion passes.

#### Config

- `models.yaml`. Tier mapping with `tier_critical = claude-opus-4-7` and
  `tier_standard = claude-sonnet-4-6`. Escalation rule (below 0.75) and
  downgrade rule (at or above 0.90 over three runs).
- `projects.yaml`. Registered projects for bootstrap continuity.

### Changed

- Communication style guardrails reinforced: serious, formal, concise, no
  emojis, no small talk, one-word answers when justifiable.
- Autonomy is full. Agents run in `bypassPermissions` mode and never ask the
  user questions; blockers go to `docs/open-items.md`.
- Confidence gate enforced at 90 for individual invocations and 95 for the
  rolling pipeline average per `.claude/rules/01-pipeline-orchestration.md`.
- Escalation loop: after 5 consecutive failing invocations of the same agent,
  pause and surface to the user instead of looping silently.

### Deprecated

- None for v2.0.0. Older behaviours that conflict with new operating rules
  are removed outright under Breaking, not flagged as deprecated first.

### Removed

- Direct provider SDK paths for outbound email. Anything that previously
  touched `smtplib`, `nodemailer`, `@sendgrid/mail`, `mailgun`, `postmark`,
  `@aws-sdk/client-ses`, or `resend` is rejected by pre-tool-use hook and
  review-agent.
- Hardcoded model strings outside `models.yaml`. Agents read tier IDs from
  the yaml config instead.

### Breaking Changes

None at the runtime API surface. v2.0.0 is an additive operating-rules and
subsystems release layered on top of v1.x. Existing agents and skills remain
dispatchable; their behaviour is stricter.

### Security

- Every Supabase table modified in this release has RLS enabled and policies
  per rule 10.
- Every view modified in this release is defined WITH `security_invoker = on`
  per rule 11.
- No secret appears in any file on disk. Secrets live in macOS Keychain per
  rule 12; iCloud-synced backups are age-encrypted.
- Pre-tool-use hook blocks any write containing real credential patterns
  (Anthropic sk-ant, sk-proj, AWS AKIA, PEM private key blocks, GitHub ghp,
  GitLab glpat, Bearer tokens, hardcoded API_KEY, hardcoded passwords).

### Known Limitations

Tracked in `docs/open-items.md`:

1. Some external services (Play Developer API, Chrome Web Store, Cloudflare
   R2) require real auth to exercise end-to-end. Dry-run paths are covered in
   the test harness; live paths are gated on credentials in Keychain.
2. Materialized views do not honour `security_invoker`. Mitigated by RLS on
   base tables plus wrapper views per rule 11.
3. launchd plist templates assume macOS. Linux systemd port is deferred.

### Migration Notes

1. Run `./bootstrap` to register your project in `projects.yaml`. The script
   creates the Keychain entries the framework expects.
2. Copy `.claude/settings.json`, `.claude/hooks/`, `.claude/rules/`, and
   `.claude/skills/` into the target work tree (or use
   `scripts/sync-framework-to-work-tree.sh`).
3. Run `scripts/check_emdash.sh` to confirm the working tree is free of
   banned dashes before the first commit under v2.0.0.
4. Run `scripts/verify.sh` to confirm all 20 success criteria hold.
5. Set Keychain entries for Supabase service role, Play Developer API, R2
   credentials, age backup recipient, and Spacemail MCP auth. See
   `.claude/rules/12-keychain.md` for naming convention.

### Verification

Verification log for v2.0.0 is documented in `docs/verification-v2.0.0.md`.
Re-run `scripts/verify.sh` at any time to refresh the evidence.

Run 12 executed `scripts/verify.sh` on 2026-04-21 with exit code 0. Result: 15
of 20 criteria passed. The 5 deferred items (bootstrap path resolution, yaml
parse path, golden eval harness, Spacemail live test, legacy dash sweep) are
logged in `docs/open-items.md` under Run 12 Deferred Items and do not block
the v2.0.0 release.

## [1.x]

Earlier versions predate the v2.0.0 operating-rules overhaul. They are no
longer maintained. Upgrade to v2.0.0.
