# System Specification - Multi-Agent Framework

A complete walkthrough of how this repository's multi-agent pipeline operates: what lives where, how a user request is transformed into code, how data is passed between agents, how skills plug in, and how hooks enforce invariants.

---

## 1. Top-Level Layout

```
opencode-framework/
├── CLAUDE.md              # Project rules loaded into every Claude Code session
├── AGENTS.md              # Mirror for non-Claude harnesses
├── README.md              # Human orientation
├── specs.md               # THIS FILE
├── docs/                  # Reference docs (rules, flow diagrams)
├── scripts/               # Sync scripts (mirror .claude → .opencode, etc.)
└── .claude/
    ├── settings.json      # Hooks, permissions, defaults
    ├── agents/            # 85 agent definitions (*.md with YAML frontmatter)
    ├── rules/             # 8 rule files (auto-loaded via CLAUDE.md)
    ├── skills/            # 130 domain skills (SKILL.md per folder)
    ├── commands/          # Slash-command definitions (/pipeline, /status, etc.)
    └── hooks/             # Shell/Python hooks for observability, security,
                           # validation, quality gates
```

There is a parallel `.opencode/` tree that mirrors `.claude/` for the opencode harness; the `.claude/` tree is the source of truth and the sync script in `scripts/` pushes changes to the mirror.

---

## 2. The Two Role Models

The framework runs under two distinct contracts:

### 2.1 Claude Code (main IDE session)
- The main session has the **full tool suite** (Read, Edit, Write, Bash, Grep, Glob, Agent, TodoWrite).
- For engineering/repo work it **must drive the pipeline** by dispatching subagents with the `Agent` tool (`subagent_type: "<agent-name>"`).
- It is the *orchestrator* - it does not write production code itself.
- The only legal user-interaction point is Stage 4 (present TaskSpec in a plain response).

### 2.2 Strict Orchestrator (Cursor / composer mode)
- Only two tools allowed: `Task` and `TodoWrite`.
- All reading/editing/executing must be delegated to subagents.
- Same pipeline, just enforced via tool restriction rather than convention.

Both modes follow the same agent definitions and rules.

---

## 3. The Mandatory Pipeline

Every engineering request flows through 16 stages. Stages marked `*` always run; stages without `*` are conditional (skip when there are no code changes to implement).

| Stage | Agent | Mode | Output |
|-------|-------|------|--------|
| -2 | pipeline-scaler | * | ScalingPlan (N runs, feature partition) |
| -1 | prompt-optimizer | * | XML-structured prompt for task-breakdown |
| 0 | task-breakdown | * | TaskSpec (features F1..Fn, acceptance criteria) |
| 0+ | orchestrator confirmation | * | User confirms TaskSpec (the ONE user touch) |
| 1 | code-discovery | * | RepoProfile (paths, patterns, conventions) |
| 2 | plan-agent | * | ImplementationPlan (micro-batches of 1-2 files, skill tags) |
| 3 | docs-researcher | * | DocsReport (library syntax via Context7 MCP) |
| 3.5 | pre-flight-checker | * | Environment/dependency sanity check |
| 4 | build-agent-N | conditional | File writes + BuildReport |
| 4.5 | test-writer | conditional | Real tests mapped to acceptance criteria |
| 5 | debugger | * | Fixes + Debugger Ledger |
| 5.5 | logical-agent | conditional | Logic verification (read-only) |
| 6 | test-agent | conditional | Test run report |
| 6.5 | integration-agent | conditional | Integration test results |
| 7 | review-agent | * | Review against TaskSpec acceptance criteria |
| 8 | decide-agent | * | `COMPLETE` or `RESTART` |

The pipeline ends only when `decide-agent` emits `COMPLETE`. `RESTART` loops back to a failing stage (or the whole pipeline) with feedback injected into the prompt.

### 3.1 Multi-Run Wrapping
If `pipeline-scaler` returns `N > 1`, the above pipeline becomes the **inner pipeline** run once per `R ∈ [1..N]`. Rules in `06-multi-run-orchestration.md`:
- Each inner run's task-breakdown is scoped to its own feature slice.
- User confirmation only happens for Run 1.
- Context (files modified, features completed) accumulates and is injected into later runs.
- `RESTART` for a single run retries **only** that run - prior complete runs stay complete.
- After all runs succeed, a single cross-run `review-agent` + `decide-agent` closes the pipeline.

---

## 4. How Data Flows Between Agents

Data is passed **through agent prompts** - there is no shared mutable state object. The orchestrator accumulates a conceptual `PipelineContext` and injects the relevant slice into each dispatch.

### 4.1 Canonical Handoff Chain

```
User Request
   │
   ▼
pipeline-scaler   ──► ScalingPlan
   │
   ▼
prompt-optimizer  ──► Optimized XML prompt (saved to .claude/.prompts/{ts}_task-breakdown_stage0.md)
   │
   ▼
task-breakdown    ──► TaskSpec  ── confirmed by user ──┐
   │                                                    │
   ▼                                                    │
code-discovery    ──► RepoProfile (paths, conventions)  │
   │                                                    │
   ▼                                                    │
plan-agent        ──► ImplementationPlan (batches,      │
                       file paths, skill tags,          │
                       ≤2 files per batch)              │
   │                                                    │
   ▼                                                    │
docs-researcher   ──► DocsReport (APIs, syntax,         │
                       version pins)                    │
   │                                                    │
   ▼                                                    │
pre-flight-checker──► Pre-flight Report                 │
   │                                                    │
   ▼                                                    │
FOR EACH BATCH:                                         │
  build-agent-N   ──► Files written + BuildReport ◄─────┤ (each batch injects
                                                        │  TaskSpec+RepoProfile+
                                                        │  Plan slice+Docs+skill)
  test-writer     ──► Test files
  logical-agent   ──► Logic Report
  test-agent      ──► Test Report
  integration-agt ──► Integration Report
  review-agent    ──► Review Report (per-batch or final)
   │
   ▼
debugger (on any failure) ──► Debug Ledger, fixes
   │
   ▼
review-agent (final)
   │
   ▼
decide-agent ──► COMPLETE | RESTART
```

### 4.2 Required Context Per Stage

From `rules/04-evaluation-and-context.md`:

| Target stage | Context injected |
|--------------|------------------|
| task-breakdown | user_request |
| code-discovery | user_request, TaskSpec |
| plan-agent | user_request, TaskSpec, RepoProfile |
| docs-researcher | user_request, TaskSpec, Plan |
| build-agent | user_request, TaskSpec, RepoProfile, Plan slice, Docs, **skill name** |
| test-writer | user_request, TaskSpec, RepoProfile, BuildReports |
| debugger | user_request, TaskSpec, BuildReports, TestReport |
| logical-agent | user_request, TaskSpec, BuildReports |
| test-agent | user_request, TaskSpec, RepoProfile, BuildReports |
| review-agent | user_request, **summaries** (not raw), acceptance criteria |
| decide-agent | same as review + decision evidence |

Stages 15/16 receive **summaries**, not raw outputs, to stay under the 33K subagent output cap.

### 4.3 The REQUEST Protocol

Subagents never dispatch other agents. When an agent needs a loop-back, it emits a text block at the end of its response:

```
### REQUEST
REQUEST: debugger - 3 test failures in auth module
Context: Failures in test_jwt_verify, test_token_refresh
Priority: high
```

The orchestrator parses REQUEST tags, creates a `LoopBackTrigger`, and dispatches the requested agent with the supplied context.

### 4.4 Prompt Caching / Persistence

- `prompt-optimizer` writes its optimized prompt to `.claude/.prompts/{timestamp}_task-breakdown_stage0.md` so past optimizations can be audited.
- Pipeline state is conceptually checkpointed after each stage (schema in `.ai/schemas/pipeline-state-schema.md`), enabling resume-after-interrupt.

---

## 5. How Agents Pick Up Their Work

### 5.1 Agent Definition Format

Each agent is a markdown file in `.claude/agents/` with YAML frontmatter:

```yaml
---
name: build-agent-1
description: "Implements 1-2 files as part of the sequential build pipeline..."
model: opus           # opus | sonnet - model policy per role
color: "#c74141"
tools: Write, Read, Edit, Grep, Glob, Bash, TodoWrite
---
# Agent body - identity, anti-orchestration rules, procedure, output format,
# perfection criteria, confidence-scoring rubric, request whitelist
```

At session start, Claude Code loads every agent in `.claude/agents/` and exposes them by `name` for dispatch via `subagent_type`.

### 5.2 Dispatch Mechanics

The orchestrator's dispatch call:

```
Agent tool:
  subagent_type: "build-agent-3"     # must match frontmatter `name`
  description: "Implement batch 3"    # 3-5 words; required by runtime
  prompt: "<XML or markdown with all needed context>"
```

The agent's `model` and `tools` come from its frontmatter and **must not** be overridden in the call.

### 5.3 What an Agent Does on Invocation

Standard subagent procedure (per `.claude/agents/*.md` bodies):
1. Read the injected `ACM` block (anti-destruction rules, safety).
2. Read its prompt (context from prior stages).
3. If `skill: <name>` is present in the prompt, read `.claude/skills/<name>/SKILL.md` before any implementation.
4. Execute its single responsibility (scan, plan, implement, debug, test, etc.).
5. Emit its structured output in the exact format the agent body prescribes.
6. **Always** emit a `### CONFIDENCE` block as the final output.

---

## 6. How Build Agents Code

Build agents (`build-agent-1` … `build-agent-55`, all `opus`) are the only agents that write production code.

### 6.1 Micro-Batch Philosophy
- Each invocation is limited to **1-2 files**.
- `plan-agent` is required to produce plans where each batch is ≤ 2 files.
- Large features use many batches, not one giant batch - e.g., a 12-file feature uses 6-12 build-agent invocations.
- Build agents **cycle**: `build-agent-1 → build-agent-2 → ... → build-agent-55 → build-agent-1 → ...` until the plan is exhausted.

### 6.2 Per-Batch Sub-Pipeline
Around each build-agent call, the orchestrator runs a nested sub-pipeline (`rules/03-agent-dispatch.md`):

```
PRE-CHECKS:   code-discovery refresh → docs-check → pre-flight validation
BUILD:        build-agent-N writes 1-2 files
POST-CHECKS:  test-writer → logical-agent → test-agent →
              integration-agent → review-agent
DEBUG LOOP:   on failure → debugger → re-run post-checks
```

### 6.3 The Build Agent's Internal Workflow
From `build-agent-*.md`:
1. **Read the spec** (target file path, requirements, constraints).
2. **Gather context** (Read referenced files, Grep patterns, Glob neighbors).
3. **Infer conventions** (imports, naming, error handling).
4. **If Flutter project**: load `.claude/rules/07-flutter-best-practices.md` first (const constructors, widget class extraction, Drift over Isar/Hive, PopScope, etc.).
5. **If `skill: X` in prompt**: Read `.claude/skills/X/SKILL.md` and follow its guidance.
6. **Implement** (Write for new files, Edit for existing - enforced by hook).
7. **Verify** (syntax check via `bash -n`, `python3 -m py_compile`, `json.tool`, etc.).
8. **Emit BuildReport**: files modified, compliance checklist, deviations, quality check outputs.
9. **Emit CONFIDENCE block**.

### 6.4 Anti-Destruction Rules (universal)
Enforced by every agent and by hooks:
- **READ before EDIT** - never modify without reading first.
- **EDIT not WRITE** - Write only for genuinely new files; the `PreToolUse/Write` hook blocks Write on existing paths.
- **No unnecessary files**.
- **Real tests** - new files need ≥ 3 real test functions with actual assertions.
- **Right-sized change** - no scope creep, no half-measures.

---

## 7. Skills - What They Are and How They're Invoked

### 7.1 Structure
- 130 domain skills live under `.claude/skills/<skill>/SKILL.md`.
- Each `SKILL.md` has YAML frontmatter (`name`, `description`) plus a body that defines exactly what the skill produces, what it **must not** do, required file outputs, and type-ID conventions (e.g., Hive `typeId` ranges per domain).
- `.claude/skills/INDEX.md` is the master index.

Example domains (each with ~6 skills: schema, provider, flow, ui, guard, test):
auth, analytics, calendar, content, e-commerce, gamification, maps, media, messaging, notifications, offline-sync, onboard, payments, search, settings, social.

Plus cross-cutting skills: `api-client-agent`, `architecture-agent`, `cache-agent`, `ci-cd-agent`, `di-agent`, `env-config-agent`, `theme-agent`, `performance-agent`, `security-audit-agent`, `accessibility-agent`, `graphify` (knowledge-graph exploration), etc., and critics: `architecture-critic`, `completeness-critic`, `consistency-critic`, `code-style-critic`.

### 7.2 Assignment (plan-agent → build-agent)
- `plan-agent` tags each batch with a `**Skill:** <name>` marker in the ImplementationPlan when a domain skill applies (e.g., Batch 2 → `**Skill:** auth-provider`).
- The orchestrator **must** forward that tag into the build-agent prompt as a literal `skill: <name>` line.
- The build-agent reads `.claude/skills/<name>/SKILL.md` **before** step 4 (implement) of its workflow and follows the skill's rules.

### 7.3 Slash-Command Invocation
Many skills are also exposed as slash commands (e.g., `/auth-schema`). When a user types `/skill-name` in the main session, Claude invokes the skill via the `Skill` tool, loading that skill's instructions directly into the main conversation.

### 7.4 Skill Discovery at Runtime
The `SubagentStop` hook fires for `build-agent.*|test-writer|docs-researcher|test-agent` and runs `subagent-stop-skill-reminder.py`, which reminds the next agent which skill (if any) was active for the batch.

---

## 8. Hooks - How Invariants Are Enforced

`.claude/settings.json` registers hooks on Claude Code tool events. Hooks return JSON decisions (`approve` / `block`) that the runtime honors.

| Event | Matcher | Hook | Purpose |
|-------|---------|------|---------|
| PreToolUse | `.*` | `observability/trace-tool-call.sh` | Logs every tool call |
| PreToolUse | `Edit` | inline | Reminds: "Must Read file first this session" |
| PreToolUse | `Write` | inline | **Blocks** Write on existing files; forces Edit |
| PreToolUse | `Write\|Edit` | `security-scan.sh` | Blocks commits of secrets (Anthropic keys, AWS keys, PEM blocks, hardcoded passwords, GitHub/GitLab PATs, Bearer tokens) |
| PostToolUse | `.*` | `observability/log-response.sh` | Logs response content |
| PostToolUse | `Task` | `validate-task-output.py` | Runs agent-specific validator from `hooks/validators/validate-<agent>.sh` |
| PostToolUse | `Write` | `quality-gate.sh` | Syntax-checks `.sh`/`.py`/`.json`/`.go` on write |
| SubagentStop | `build-agent.*\|test-writer\|docs-researcher\|test-agent` | `subagent-stop-skill-reminder.py` | Carries skill context forward |
| Stop | `.*` | inline | Final approval marker |
| UserPromptSubmit | `.*` | inline | Injects `[RULES]` reminder into every prompt |

### 8.1 Validators
One shell validator per agent lives in `.claude/hooks/validators/`:
`validate-build-agent.sh`, `validate-task-breakdown.sh`, `validate-test-agent.sh`, etc. They run **after** the agent's Task call returns and can veto poor output (e.g., missing required sections, placeholder tests, wrong format).

### 8.2 Security Gate
`security-scan.sh` pattern-matches blocked secret formats in every Write/Edit payload. CLAUDE.md documents the blocked patterns as prompt-level instructions too, so the model refuses before the hook even fires.

### 8.3 Quality Gate
`quality-gate.sh` enforces syntax checks per extension:
- `.sh` → `bash -n`
- `.py` → `python3 -m py_compile`
- `.json` → `python3 -m json.tool`
- `.go` → `gofmt -l` (warn only)

If a check fails, the write is flagged and the agent must fix before proceeding.

---

## 9. Confidence Scoring (Quality Gate Between Stages)

From `rules/09-confidence-scoring.md` and enforcement in `rules/01-pipeline-orchestration.md`.

### 9.1 The CONFIDENCE Block
Every agent ends its output with:

```
### CONFIDENCE
Score: 94/100
- Completeness: 24/25
- Accuracy: 24/25
- Evidence Quality: 23/25
- Format Compliance: 23/25
Justification: <1-3 sentences>
```

Four 25-point dimensions: **Completeness**, **Accuracy**, **Evidence Quality**, **Format Compliance**.

### 9.2 Orchestrator Gate
- Score **< 90** → fail, re-dispatch the same agent with an improved prompt (do **not** instruct it to "score higher" - improve the task prompt only).
- Missing/invalid block → fail, re-dispatch.
- Rolling pipeline average < 95 → flag.
- Same agent fails 5 consecutive times → pause and surface to user.
- No cap on total reruns - persistence over quitting.

### 9.3 Anti-Cheating
- Agents do **not** know the numeric threshold.
- Agents **must** be brutally honest - deductions must enumerate specific rubric-dimension gaps so the orchestrator can write a better follow-up prompt.
- Orchestrator cannot instruct a score; it can only rewrite the prompt.

---

## 10. Slash Commands

`.claude/commands/` holds command definitions invokable as `/<name>`:
- `/pipeline` - run the full multi-agent pipeline on the current request.
- `/prompt` - invoke `prompt-optimizer` standalone.
- `/status` - print pipeline-status checklist.
- `/restart` - restart from Stage 0.

Plus domain skills (`/auth-schema`, `/analytics-flow`, …) exposed as invocable slash commands via the skill mechanism.

---

## 11. Interruption and Recovery

- **Mid-stage interrupt**: state is conceptually checkpointed; on resume the orchestrator re-enters at the last completed stage using the persisted context.
- **Agent failure (non-confidence)**: orchestrator evaluates output (`ACCEPT`/`RETRY`/`CONTINUE`/`HANDLE REQUEST`) and re-dispatches with improved prompt.
- **Confidence failure**: mandatory re-dispatch with better prompt until score ≥ 90.
- **Decide-agent `RESTART`**: loop back to the failing stage or the whole run (multi-run: just that run) with decide-agent feedback injected.
- **Context window pressure**: set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` (or 70) to compact earlier; agents pass **summaries** after Stage 14 to stay within the 33K subagent output cap.
- **User-initiated abort**: the user can interject at any time; only Stage 4 confirmation is a designed stop point.

---

## 12. Browser / Live-Site Work

Browser tasks bypass the normal first stage. `claude-in-chrome` is required whenever the user needs Chrome, a live DOM, real clicks/forms, or on-page verification. It wraps the Claude-in-Chrome MCP tools plus Read/WebSearch/WebFetch.

- **Pure browser task (no repo changes)**: dispatch `claude-in-chrome` first; skip `pipeline-scaler`.
- **Browser + code task**: run `claude-in-chrome` at the step that needs the live page, and run `pipeline-scaler` for the engineering track separately. Still one Task per response.

---

## 13. Model Policy

From CLAUDE.md:

| Role | Model |
|------|-------|
| `plan-agent`, all `build-agent-*`, all `debugger-*` | `opus` |
| `code-discovery`, `decide-agent`, `perfection-validator` | `sonnet` |
| Everything else (pipeline-scaler, task-breakdown, etc.) | `sonnet` |

Set in each agent's frontmatter; not overridden at dispatch time.

---

## 14. End-to-End Example

User: *"Add JWT login with email/password and secure token storage."*

1. `pipeline-scaler` → ScalingPlan with 1 run (scope fits a single pipeline).
2. `prompt-optimizer` → XML prompt for task-breakdown, saved to `.claude/.prompts/`.
3. `task-breakdown` → TaskSpec with F1 (schema), F2 (provider), F3 (UI), F4 (guards), F5 (tests).
4. Orchestrator shows TaskSpec to user → confirmed.
5. `code-discovery` → RepoProfile noting Flutter + Riverpod + Drift.
6. `plan-agent` → 8 batches (≤ 2 files each), each tagged with a skill (`auth-schema`, `auth-provider`, `auth-ui`, `auth-guard`, `auth-test`).
7. `docs-researcher` → flutter_secure_storage + Drift + Riverpod syntax.
8. `pre-flight-checker` → deps present, env OK.
9. For each batch: `build-agent-N` (reads the assigned skill's SKILL.md, writes the file, runs syntax check), then test-writer → logical-agent → test-agent → integration-agent → review-agent. On failure → `debugger`.
10. Final `review-agent` maps each acceptance criterion to evidence.
11. `decide-agent` → `COMPLETE` (or `RESTART` with feedback).

Every one of those dispatches carries a CONFIDENCE block; below-90 means re-dispatch. Every file write passes the security scan and quality gate hooks. Every Task return is validated by the agent-specific validator script.

---

## 15. Key Invariants (One-Line Summary)

- One Task per response. No parallelism. No `run_in_background`.
- One user confirmation (after task-breakdown). Everything else is autonomous.
- Orchestrator never writes code. Build agents do.
- Each build agent handles ≤ 2 files and must activate the assigned skill.
- Every agent output ends with a `### CONFIDENCE` block; < 90 = rerun.
- Hooks enforce: Write blocked on existing files; secrets blocked; syntax checked; validators run per agent.
- Pipeline stops only on `decide-agent: COMPLETE`. No retry caps.
