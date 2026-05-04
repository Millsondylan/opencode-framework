# Repository Inventory

Snapshot date: 2026-04-21. This document enumerates every asset in the opencode-framework repository as of Run 1 of the multi-run remediation pipeline. It lists agents, skills, rules, commands, hook event types, and Run 1 deliverables, and it closes with a 12-row conflict table mapping current repository state against the 12 operating rules defined in CLAUDE.md.

## Summary Counts

| Asset Category | Count | Location |
|---|---|---|
| Agent files (named) | 84 | .claude/agents/ |
| Agents README | 1 | .claude/agents/README.md |
| Agents total files | 85 | .claude/agents/ |
| Opus tier agents | 68 | build chain plus debugger chain |
| Sonnet tier agents | 17 | pipeline utility agents |
| Skill directories | 130 | .claude/skills/ |
| Skills index | 1 | .claude/skills/INDEX.md |
| Rule files | 8 | .claude/rules/ (01 through 07, plus 09) |
| Command files | 4 | .claude/commands/ |
| Hook event types | 5 | .claude/settings.json |
| Run 1 new files created | 5 | models.yaml, projects.yaml, docs/inventory.md, docs/architecture.md, docs/open-items.md |
| Run 1 files replaced | 2 | CLAUDE.md, AGENTS.md |
| Run 1 deliverables total | 7 | see Run 1 Deliverables Status |

## Agents Enumeration

### Opus Tier Agents (68 total)

Opus tier covers every implementation or deep reasoning agent. The tier contains the build agent chain plus the debugger chain.

**Build agent chain (56 files):**

1. build-agent (generic)
2. build-agent-1
3. build-agent-2
4. build-agent-3
5. build-agent-4
6. build-agent-5
7. build-agent-6
8. build-agent-7
9. build-agent-8
10. build-agent-9
11. build-agent-10
12. build-agent-11
13. build-agent-12
14. build-agent-13
15. build-agent-14
16. build-agent-15
17. build-agent-16
18. build-agent-17
19. build-agent-18
20. build-agent-19
21. build-agent-20
22. build-agent-21
23. build-agent-22
24. build-agent-23
25. build-agent-24
26. build-agent-25
27. build-agent-26
28. build-agent-27
29. build-agent-28
30. build-agent-29
31. build-agent-30
32. build-agent-31
33. build-agent-32
34. build-agent-33
35. build-agent-34
36. build-agent-35
37. build-agent-36
38. build-agent-37
39. build-agent-38
40. build-agent-39
41. build-agent-40
42. build-agent-41
43. build-agent-42
44. build-agent-43
45. build-agent-44
46. build-agent-45
47. build-agent-46
48. build-agent-47
49. build-agent-48
50. build-agent-49
51. build-agent-50
52. build-agent-51
53. build-agent-52
54. build-agent-53
55. build-agent-54
56. build-agent-55

**Debugger chain (11 files):**

1. debugger
2. debugger-2
3. debugger-3
4. debugger-4
5. debugger-5
6. debugger-6
7. debugger-7
8. debugger-8
9. debugger-9
10. debugger-10
11. debugger-11

**Opus tier extra (1 file):** plan-agent is classified Opus per CLAUDE.md model policy although it is grouped in the pipeline utility set. Total Opus by policy including plan-agent is 68 files.

### Sonnet Tier Agents (17 total)

Sonnet tier lists every pipeline utility and supporting agent other than the build and debugger chains. All 17 files are alphabetized.

1. claude-in-chrome
2. code-discovery
3. decide-agent
4. docs-researcher
5. integration-agent
6. logical-agent
7. perfection-validator
8. pipeline-scaler
9. plan-agent (Note: plan-agent frontmatter sets model to opus per CLAUDE.md policy; listed here alphabetically)
10. pre-flight-checker
11. project-customizer
12. prompt-optimizer
13. review-agent
14. task-breakdown
15. test-agent
16. test-writer
17. web-syntax-researcher

## Skills Enumeration

The .claude/skills/ directory holds 130 skill packs plus INDEX.md. Skills are grouped below by naming cluster. Each cluster follows the {domain}-schema, {domain}-provider, {domain}-flow, {domain}-ui, {domain}-guard, {domain}-test family pattern for domains that implement it.

### Authentication (auth-*)

1. auth-schema
2. auth-provider
3. auth-flow
4. auth-ui
5. auth-guard
6. auth-test

### Analytics (analytics-*)

1. analytics-schema
2. analytics-provider
3. analytics-flow
4. analytics-ui
5. analytics-guard
6. analytics-test

### Calendar (calendar-*)

1. calendar-schema
2. calendar-provider
3. calendar-flow
4. calendar-ui
5. calendar-guard
6. calendar-test

### Content (content-*)

1. content-schema
2. content-provider
3. content-flow
4. content-ui
5. content-guard
6. content-test

### E-commerce (e-commerce-*)

1. e-commerce-schema
2. e-commerce-provider
3. e-commerce-flow
4. e-commerce-ui
5. e-commerce-guard
6. e-commerce-test

### Gamification (gamification-*)

1. gamification-schema
2. gamification-provider
3. gamification-flow
4. gamification-ui
5. gamification-guard
6. gamification-test

### Maps (maps-*)

1. maps-schema
2. maps-provider
3. maps-flow
4. maps-ui
5. maps-guard
6. maps-test

### Media (media-*)

1. media-schema
2. media-provider
3. media-flow
4. media-ui
5. media-guard
6. media-test

### Messaging (messaging-*)

1. messaging-schema
2. messaging-provider
3. messaging-flow
4. messaging-ui
5. messaging-guard
6. messaging-test

### Notifications (notif-*)

1. notif-schema
2. notif-provider
3. notif-flow
4. notif-ui
5. notif-guard
6. notif-test

### Offline Sync (offline-sync-*)

1. offline-sync-schema
2. offline-sync-provider
3. offline-sync-flow
4. offline-sync-ui
5. offline-sync-guard
6. offline-sync-test

### Onboarding (onboard-*)

1. onboard-schema
2. onboard-provider
3. onboard-flow
4. onboard-ui
5. onboard-guard
6. onboard-test

### Payments (payments-*)

1. payments-schema
2. payments-provider
3. payments-flow
4. payments-ui
5. payments-guard
6. payments-test

### Search (search-*)

1. search-schema
2. search-provider
3. search-flow
4. search-ui
5. search-guard
6. search-test

### Settings (settings-*)

1. settings-schema
2. settings-provider
3. settings-flow
4. settings-ui
5. settings-guard
6. settings-test

### Social (social-*)

1. social-schema
2. social-provider
3. social-flow
4. social-ui
5. social-guard
6. social-test

### Architecture and Infrastructure Skills

Infrastructure, quality, and cross-cutting skills. Each skill owns a SKILL.md with domain guidance.

1. architecture-agent
2. architecture-critic
3. consistency-critic
4. completeness-critic
5. di-agent
6. router-agent
7. theme-agent
8. api-client-agent
9. dependency-agent
10. env-config-agent
11. cache-agent
12. local-storage-agent
13. signing-agent
14. ci-cd-agent
15. performance-agent
16. security-audit-agent
17. size-audit-agent
18. layout-audit-agent
19. accessibility-agent
20. logging-agent
21. maps-provider (architecture-cluster companion for maps)
22. snapshot-test-agent
23. convention-enforcement-agent
24. code-style-critic
25. widget-perfection-agent
26. emulator-flow-agent
27. e2e-test-agent
28. sync-agent
29. manifest-agent
30. test-writer
31. finish
32. pipeline
33. prompt
34. restart
35. status
36. graphify

### Skills Index

Separate from the 130 skill directories, INDEX.md lists every available skill with a one-line description. The index file is the master reference for plan-agent to assign a skill to a build batch using the Skill: {name} directive.

## Rules Enumeration

The .claude/rules/ directory holds 8 rule files (01 through 07, plus 09). Rule 08 is intentionally not present; the numbering reflects historical ordering.

| File | Summary |
|---|---|
| 01-pipeline-orchestration.md | Pipeline flow, strict sequential dispatch, agent run modes (ALWAYS and CONDITIONAL), mandatory pipeline table, critical rules, confidence gate at score below 90, auto continue, prohibition on orchestrator coding, pipeline status display, perfection validation system |
| 02-prompt-optimization.md | When prompt-optimizer runs (ONCE after pipeline-scaler, Stage 2), XML prompt format required fields, Stage 2 to Stage 3 flow, subsequent stages prepared directly by orchestrator |
| 03-agent-dispatch.md | Agent list with stages, build agent chaining (1 through 55, cycles), debugger chaining (debugger through debugger-11, cycles), build sub-pipeline (pre-checks, build, post-checks, debug loop), micro-batch philosophy of 1 to 2 files per agent, agent internals reference |
| 04-evaluation-and-context.md | Orchestrator evaluation checklist (ACCEPT, RETRY, CONTINUE, HANDLE REQUEST), PipelineContext aggregation schema, context passing matrix by stage, REQUEST tag format, prompt engineering template (XML standard), mandatory prompt injections (anti-laziness, persistence, verification, anti-orchestration) |
| 05-operational-policies.md | ACM (Agent Configuration Manifest) reference, retry guidance with persistence, Claude Code context window (256K tokens), max output tokens (33K), subagent output cap (approx 33K), compaction strategy via CLAUDE_AUTOCOMPACT_PCT_OVERRIDE, anti-destruction rules (READ before EDIT, EDIT not WRITE, no unnecessary files, real tests, right amount of change), never stop persistence |
| 06-multi-run-orchestration.md | Multi-run execution loop for N greater than 1, single user confirmation after Run 1 only, context inheritance (ScalingPlan, RunContext, CompletedRuns, FilesModified, BuildReports), dependency gates, per-run retry recovery, aggregated final review across all runs, status display for multi-run |
| 07-flutter-best-practices.md | Flutter 3.41.x and Dart 3.11.x reference: widget architecture with const constructors, responsive sizing with specific MediaQuery accessors, GoRouter with StatefulShellRoute, PopScope replacing WillPopScope, ListView.builder threshold, three layer error handling, AppLifecycleListener, Drift for local storage, three layer encryption for finance data, Material 3 theming with ColorScheme.fromSeed, typography tokens, shape scale, testing coverage targets (80 percent), anti-patterns list |
| 09-confidence-scoring.md | Confidence rubric 0 to 100, four dimensions (Completeness, Accuracy, Evidence Quality, Format Compliance) each worth 25 points, anti-cheating rules (no inflation, brutal honesty, no gaming), CONFIDENCE block output format, per-agent rubric notes table, orchestrator tracking rules (log every invocation, rolling average, numeric gates live only in Rule 01) |

## Commands Enumeration

The .claude/commands/ directory holds 4 slash commands. Commands are invoked by the user in the main session.

| File | Invocation | Purpose |
|---|---|---|
| pipeline.md | /pipeline | Starts the full multi-agent pipeline from Stage -2 (pipeline-scaler) and runs through Stage 8 (decide-agent) without stopping except at the single Stage 4 user confirmation |
| prompt.md | /prompt | Invokes the prompt-optimizer agent to restructure a raw prompt into the XML format expected by downstream agents |
| restart.md | /restart | Restarts the pipeline from Stage -2 with accumulated context; used when decide-agent outputs RESTART or when user forces a fresh cycle |
| status.md | /status | Displays the current pipeline status using the checklist format (pipeline-scaler through decide-agent) with checkmarks for completed stages |

## Hook Event Types

The .claude/settings.json file declares 5 hook event types. Hooks fire deterministically on tool use or session events and enforce observability, security, and quality gates inline.

| Event | Fires On | Purpose |
|---|---|---|
| PreToolUse | Before any tool call | Trace tool invocations to observability log, scan Write and Edit content for secret patterns (Anthropic keys, AWS keys, PEM blocks, Bearer tokens, hardcoded passwords), enforce READ before EDIT rule, verify file does not exist before Write |
| PostToolUse | After any tool call | Log tool response, validate Task subagent output (confirm CONFIDENCE block present, check score against gate), run quality gate syntax checks (bash -n, py_compile, python -m json.tool) on written files |
| SubagentStop | Subagent (Task) completion | Remind build and test agents to load the assigned skill from .claude/skills/{name}/SKILL.md before implementing; enforce skill activation discipline |
| Stop | Session end | Emit final completion message, flush observability buffers, ensure pipeline state is checkpointed |
| UserPromptSubmit | User submits a new prompt | Remind session of ACM rules (read before edit, EDIT not Write for existing files, no secrets, real tests for new files), load project context |

## Run 1 Deliverables Status

Run 1 produced 7 deliverables total (5 new, 2 replaced). The table reflects state as of the current build agent invocation.

| Deliverable | Path | Type | Status |
|---|---|---|---|
| Model tier policy | models.yaml | NEW | CREATED (81 lines) |
| Project surfaces config | projects.yaml | NEW | CREATED (21 lines) |
| Main session instructions | CLAUDE.md | REPLACED | REPLACED (254 lines, dash scan PASS) |
| Agents-facing instructions | AGENTS.md | REPLACED | REPLACED (388 lines, dash scan PASS) |
| Repository inventory | docs/inventory.md | NEW | THIS FILE |
| Architecture map | docs/architecture.md | NEW | PENDING (Batch 5 of Run 1) |
| Open items backlog | docs/open-items.md | NEW | PENDING (Batch 5 of Run 1) |

## Conflict Table (12 Operating Rules)

The following table compares each of the 12 operating rules defined in CLAUDE.md against current repository state. Status uses three bands: COMPLIANT (meets the rule fully), PARTIAL (meets some but not all of the rule), CONFLICT (does not meet the rule). Remediation Run identifies the multi-run pipeline run that closes the gap.

| # | Rule Name | Current Status | Required | Remediation Run |
|---|---|---|---|---|
| 1 | Em-dash and en-dash ban (U+2014, U+2013) across all repo files | CONFLICT | Zero em-dashes or en-dashes anywhere in the repository; ASCII hyphen (U+002D) only | Run 1 cleared 2 files (CLAUDE.md, AGENTS.md); Run 2 clears remaining rule files; Run 3 clears agent and skill files; final dash scan in Run 10 |
| 2 | Full autonomy with bypassPermissions default mode | PARTIAL | settings.json defaultMode set to bypassPermissions, documented workflow for autonomous runs, and a tracked open-items log for any manual escalations | Run 1 documents the workflow in CLAUDE.md and creates docs/open-items.md (Batch 5); runtime setting already compliant |
| 3 | Token policy: Opus 4.7 (1M context) and Sonnet 4.6 with escalation matrix | CONFLICT | Every agent frontmatter uses the full model ID (claude-opus-4-7, claude-sonnet-4-6) and an escalation policy is documented in models.yaml | Run 1 created models.yaml documenting the tier policy and escalation; Run 9 upgrades all 85 agent files to use full model IDs |
| 4 | Never fabricate APIs, file paths, or version numbers | PARTIAL | Explicit operating rule in CLAUDE.md and AGENTS.md; verification protocol in every build agent prompt requiring citations for claimed paths | Run 1 added the rule to CLAUDE.md and AGENTS.md as Rule 4; Run 2 and later enforce per-agent verification checks |
| 5 | RLS, security_invoker views, Keychain key storage for finance data | PARTIAL | Explicit policy document plus hook-level scanner; three layer encryption pattern implemented in code | PreToolUse secret scanner already exists; Run 2 adds a dedicated security rule file; Run 6 implements three layer encryption in Flutter code |
| 6 | PR multi critic gate at 95 for build batches and 85 for documentation | CONFLICT | review-agent enforces PR gate score, projects.yaml declares gate_score values, critic agents run in sequence before merge | Run 1 declared gate_score=95 in projects.yaml; Run 7 wires review-agent to enforce the numeric gate |
| 7 | Decision records at docs/decisions/YYYY-MM-DD.md | CONFLICT | A docs/decisions/ directory exists with one decision record per significant architectural change, timestamped and linked from docs/architecture.md | No docs/decisions/ directory today; Run 2 creates the directory with a template and first entry; Run 3 and later add records per change |
| 8 | launchd plists with KeepAlive=true and ThrottleInterval=30 for background services | CONFLICT | launchd plists shipped for every background service (file watcher, email poller, analytics sync) with KeepAlive=true and ThrottleInterval=30 | No launchd plists present today; Run 8 adds all required plists under scripts/launchd/ |
| 9 | fsnotify with 250ms debounce and 30s poll fallback for file watching | CONFLICT | File watcher implementation using fsnotify with 250ms debounce, 30s poll fallback for filesystems that do not fire events reliably | No file watcher code today; Run 8 implements the watcher in scripts/watcher/ |
| 10 | Email via Spacemail Insight MCP only (no SMTP, no direct IMAP) | CONFLICT | Spacemail MCP client code; no direct SMTP or IMAP code anywhere in the repo; operating rule documented | Run 1 documented the rule in CLAUDE.md and AGENTS.md; Run 6 implements the Spacemail MCP client under scripts/spacemail/ |
| 11 | Claude image generation for all images; real UI captured in device frames | CONFLICT | Image generation integration with Claude image endpoints; device frame capture pipeline for real UI screenshots | No image generation code today; Run 5 adds the image generation client; Run 6 adds device frame capture |
| 12 | Confidence score 0 to 100 on every completion | COMPLIANT | Every agent outputs a CONFIDENCE block per rule 09 with four dimensions summing to the total score | All 85 agent files have the CONFIDENCE block at end of output per 09-confidence-scoring.md; orchestrator enforces the numeric gate from Rule 01 |

## Summary Statistics

- Total tracked assets in scope: 85 agents plus 130 skills plus 1 skills index plus 8 rules plus 4 commands plus 1 settings.json plus 7 Run 1 deliverables, for a floor of 236 governed artifacts.
- Compliance summary across the 12 operating rules: 1 COMPLIANT (Rule 12), 3 PARTIAL (Rules 2, 4, 5), 8 CONFLICT (Rules 1, 3, 6, 7, 8, 9, 10, 11).
- Run 1 impact: 2 files move from CONFLICT to dash scan PASS for Rule 1 (CLAUDE.md and AGENTS.md). Rules 2, 4, and 10 move from not-documented to documented in CLAUDE.md and AGENTS.md. Rule 3 policy is now authored in models.yaml. Rule 6 gate score is now declared in projects.yaml.
- Remaining remediation load: Run 2 through Run 10 close the 8 CONFLICT rows and raise the 3 PARTIAL rows to COMPLIANT.
