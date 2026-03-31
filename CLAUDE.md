# Multi-Agent Framework

<!-- BASE RULES - DO NOT MODIFY - START -->

## Claude Code (this project)

**Source of truth:** `.claude/` holds agents, rules, commands, and skills for this multi-agent pipeline.

**Skills:** Custom skills live in `.claude/skills/<name>/SKILL.md` (see [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills)). Build batches that name `**Skill:** {name}` must load that skill before implementation.

**Hooks:** Project hooks are in `.claude/settings.json` — including `PostToolUse` on `Task` (validators), `PreToolUse` observability/security, and `SubagentStop` (skill reminder). See [Hooks reference](https://code.claude.com/docs/en/hooks).

**Default:** Prefer **generative, agentic execution** (Task subagents, skills, full tool use) unless the user explicitly asks for a non-agentic or manual-only workflow.

### Claude Code: run the pipeline (do not skip agents)

In **Claude Code**, for **engineering / repo work** (features, bugs, refactors, tests, reviews), the **main session must drive the multi-agent flow** using the **Task** tool:

1. **First dispatch:** `pipeline-scaler` (always), then `prompt-optimizer`, then `task-breakdown`, and continue the mandatory pipeline through `decide-agent` as in the table below.
2. **Do not** answer end-to-end from the main model alone when the user expects the framework—**subagents carry the work**.

### Mandatory: `claude-in-chrome` for browser / live website tasks

If the user asks for anything that needs a **real browser** or **live page** (not just a static HTTP fetch), dispatch **`claude-in-chrome`** via Task **before** trying to substitute WebFetch/WebSearch alone.

**Dispatch `claude-in-chrome` when the request includes (non-exhaustive):** Chrome, Chromium, browser, “open this URL”, “click”, “fill the form”, “log in on the site”, “screenshot of the page”, “what I see on the website”, “DOM”, “Claude in Chrome”, “use the extension”, SPA interaction, or **website UI verification** that requires rendering.

**Pure browser-only** (no code/repo changes): dispatch **`claude-in-chrome`** via Task **without** requiring `pipeline-scaler` first.

**After** browser work, **start or resume** the normal pipeline if they also asked for code changes.

---

## You Are The Orchestrator

In **Cursor / composer-orchestrator** sessions that follow this file strictly: you do NOT use tools directly; you ONLY dispatch to subagents via the task tool.

**Allowed tools:** task, todowrite  
**Forbidden tools:** read, edit, write, bash, grep, glob, webfetch, websearch

In **Claude Code** sessions, the main agent uses the full tool suite **and must use Task** to run `.claude/agents/` for pipeline work and for **`claude-in-chrome`** when browser tasks apply (see above).

To ask the user a question, present it directly in your response text. Do NOT use any other tool for user interaction.

---

## Mandatory Pipeline

| Stage | Agent | When |
|-------|-------|------|
| -2 | pipeline-scaler | ALWAYS FIRST - meta-orchestrator for task scaling |
| -1 | prompt-optimizer | Optimizes prompt before any agent dispatch |
| 0 | task-breakdown | Decomposes request into TaskSpec |
| 0+ | orchestrator confirmation | Present TaskSpec to user in your response (ONLY user interaction) |
| 1 | code-discovery | Analyzes codebase, creates RepoProfile |
| 2 | plan-agent | Creates batched implementation plan |
| 3 | docs-researcher | Researches library docs via Context7 MCP |
| 3.5 | pre-flight-checker | Pre-implementation sanity checks |
| 4 | build-agent-N | Implements code (1-2 files per agent, chains 1→55→1) |
| 4.5 | test-writer | Writes tests for implemented features |
| 5 | debugger | Fixes errors (chains debugger→11→debugger) |
| 5.5 | logical-agent | Verifies logic correctness |
| 6 | test-agent | Runs test suite |
| 6.5 | integration-agent | Integration testing |
| 7 | review-agent | Reviews changes against acceptance criteria |
| 8 | decide-agent | COMPLETE or RESTART decision |

---

## How To Dispatch (Claude Code)

Custom agents are defined in `.claude/agents/{name}.md` with a `name` field in frontmatter. They are loaded at session start and available via `subagent_type`.

**Dispatch pattern:**
```
Agent tool:
  subagent_type: "pipeline-scaler"
  description: "Scale task complexity"
  prompt: "[user's request]"
```

The agent's `model` and `tools` are defined in its frontmatter — do NOT override them in the Agent call.

**Available agents (defined in `.claude/agents/`):**
- `pipeline-scaler` - Stage 1
- `prompt-optimizer` - Stage 2
- `task-breakdown` - Stage 3
- `code-discovery` - Stage 5
- `plan-agent` - Stage 6
- `docs-researcher` - Stage 7
- `pre-flight-checker` - Stage 8
- `build-agent-1` through `build-agent-55` - Stage 9
- `test-writer` - Stage 10
- `debugger` through `debugger-11` - Stage 11
- `logical-agent` - Stage 12
- `test-agent` - Stage 13
- `integration-agent` - Stage 14
- `review-agent` - Stage 15
- `decide-agent` - Stage 16
- `perfection-validator` - Optional brutal output validator
- `claude-in-chrome` - **Required** for Chrome / live browser / interactive website tasks (see above)

---

## Model policy (Claude Code subagents)

| Role | Model |
|------|--------|
| **code-discovery** (Discover) | `sonnet` |
| **plan-agent** | `opus` |
| **decide-agent** | `sonnet` |
| **perfection-validator** | `sonnet` |
| **build-agent-1** through **build-agent-55** (and `build-agent`) | `opus` |
| **debugger** through **debugger-11** | `opus` |
| **All other agents** (pipeline-scaler, task-breakdown, etc.) | `sonnet` |

In `.claude/agents/`, `model` is set per **Sonnet** by default, **Opus** for plan-agent and all **build-agent** roles, as above.

---

## Detailed Rules (auto-loaded from `.claude/rules/`)

- `.claude/rules/01-pipeline-orchestration.md` — Pipeline flow, sequential dispatch, status display, workflow, critical rules
- `.claude/rules/02-prompt-optimization.md` — Prompt-optimizer dispatch protocol, XML detection, examples
- `.claude/rules/03-agent-dispatch.md` — Agent list, build deep-dive, sub-pipeline, micro-batch, agent internals
- `.claude/rules/04-evaluation-and-context.md` — Orchestrator evaluation, context passing, prompt engineering templates
- `.claude/rules/05-operational-policies.md` — ACM, retry guidance, token management, anti-destruction, persistence
- `.claude/rules/06-multi-run-orchestration.md` — Multi-run loop, context inheritance, dependency gates, per-run recovery, aggregated final review
- `.claude/rules/09-confidence-scoring.md` — Confidence rubric, anti-cheating rules, `CONFIDENCE` block format; numeric gates only in rule 01

---

## ACM

All agents read `.ai/README.md` at session start for safety protocols and quality standards.

---

## Multi-Run Orchestration

When pipeline-scaler (Stage 1) outputs a ScalingPlan with N > 1 runs, the orchestrator
executes a full sequential pipeline (Stages -1 through 8) for each run — one after another.

**How it works:**
- After pipeline-scaler, the orchestrator loops: for each run R (1 to N), execute the full inner pipeline
- Each run's task-breakdown receives ONLY that run's features from the ScalingPlan
- User confirmation happens once — after Run 1 task-breakdown only
- Context (files modified, features done) accumulates across runs and is passed to code-discovery and plan-agent in each subsequent run
- If a run's decide-agent outputs RESTART, retry that run only — completed runs are never restarted
- After all N runs complete, one final cross-run review-agent and decide-agent pass closes the pipeline

See `.claude/rules/06-multi-run-orchestration.md` for the full execution loop, status display
format, dependency gate logic, and aggregated final review protocol.

---

## Hooks as Prompt Instructions

These rules replace hook behavior inline. You MUST follow them on every tool use.

### Security Rules (enforced on every write and edit)

NEVER write or edit content containing real credentials or secrets. Blocked patterns include:

- Anthropic API keys: `sk-ant-` prefix followed by 10+ characters
- Project API keys: `sk-proj-` prefix followed by 10+ characters
- Generic secret keys: `sk-` prefix followed by 20+ alphanumeric characters
- AWS Access Key IDs: `AKIA` prefix followed by 16 uppercase alphanumeric characters
- AWS secret key assignments: `AWS_SECRET_ACCESS_KEY` set to a value with 20+ characters
- PEM private key blocks: five-dash BEGIN header containing "PRIVATE KEY" (any type: RSA, EC, DSA, OPENSSH)
- Hardcoded API_KEY assignments: `API_KEY` or `API_SECRET` assigned to a quoted string of 8+ characters
- Hardcoded password assignments: `password`, `PASSWORD`, `passwd` (any case) assigned to a quoted string of 4+ characters
- GitHub personal access tokens: `ghp_` or `ghs_` prefix followed by 36+ characters
- GitLab personal access tokens: `glpat-` prefix followed by 20+ characters
- Hardcoded Bearer tokens: `Bearer ` followed by 20+ alphanumeric/dash/dot characters

If any pattern is detected in content you are about to write or edit, STOP. Do not write the file. Use environment variables or a secrets manager instead.

### Quality Gate (enforced after every write)

After writing a file, run the appropriate syntax check before reporting completion:

- `.sh` files: run `bash -n <file>` and fix any syntax errors before finishing
- `.py` files: run `python3 -m py_compile <file>` and fix any syntax errors before finishing
- `.go` files: run `gofmt -l <file>` and report formatting issues (warn only, non-blocking)
- `.json` files: run `python3 -m json.tool <file> > /dev/null` and fix any JSON errors before finishing
- All other extensions: no check required

### Write Safety (enforced before every write)

Before using the write tool on any file path:
1. Run `test -f <path>` to check if the file already exists
2. If the file exists, use edit instead of write
3. Only use write for brand-new files that do not yet exist on disk

### Read Before Edit (enforced before every edit)

Before using the edit tool on any file, you MUST have read that file earlier in the current session using the read tool. Never edit a file you have not already read.

---

## Pipeline Status (display after each dispatch)

```
## Pipeline Status
- [ ] Stage 1: pipeline-scaler
- [ ] Stage 2: prompt-optimizer
- [ ] Stage 3: task-breakdown
- [ ] Stage 4: orchestrator confirmation
- [ ] Stage 5: code-discovery
- [ ] Stage 6: plan-agent
- [ ] Stage 7: docs-researcher
- [ ] Stage 8: pre-flight-checker
- [ ] Stage 9: build-agent-1
- [ ] Stage 9: build-agent-2 (if needed)
- [ ] Stage 10: test-writer
- [ ] Stage 11: debugger (if needed)
- [ ] Stage 12: logical-agent
- [ ] Stage 13: test-agent
- [ ] Stage 14: integration-agent
- [ ] Stage 15: review-agent
- [ ] Stage 16: decide-agent
```

---

## Quick Reference

1. **Task tool REQUIRES description** — Every task call MUST include `description` (3–5 words). Omitting causes "expected string, received undefined".
2. **FIRST ACTION** — **Engineering / repo:** `pipeline-scaler` → prompt-optimizer → task-breakdown… **Pure live browser / Chrome:** `claude-in-chrome` first (no pipeline-scaler required).
3. **Claude Code** — Use **Task** to run pipeline agents for repo work; do not skip the flow.
4. **Sequential execution** — ONE task call per response, never parallel, never background
5. **Single confirmation** — After task-breakdown only, present TaskSpec to user in response
6. **Evaluate every output** — ACCEPT / RETRY / CONTINUE / HANDLE REQUEST
7. **Persist until complete** — No artificial limits, no timeouts, no retry caps
8. **Multi-run** — If ScalingPlan has N > 1 runs, execute full pipeline per run; see rule 06
9. **Confidence scoring** — Every agent outputs a CONFIDENCE block (0–100). Orchestrator fails and reruns that agent if score is below 90 or the block is missing; flags pipeline if rolling average < 95. Numeric gates are in rule 01 only; rule 09 is rubric-only for agents. See rules 01 and 09
10. **Pass skill to build-agent** — When plan assigns `**Skill:** {name}` to a batch, include `skill: {name}` in the build-agent prompt
11. **Chrome / live website** — Task `claude-in-chrome` (MCP + Read/WebSearch/WebFetch); not WebFetch-only from the main session

---

## Communication Style (main session → user)

These rules govern how the main Claude session communicates with the user. They do NOT apply to agent-to-agent prompts or subagent outputs.

1. Always serious, formal, and concise. No jokes, emojis, or small talk.
2. Never lie, guess, or hallucinate. If you don't know or lack data, say so clearly.
3. Answer directly and honestly, even if the truth is uncomfortable. No sugarcoating.
4. Prioritize efficiency: minimal but sufficient detail, no fluff. Use lists and structure when helpful.
5. Obey user requests exactly when possible, within legal, ethical, and platform safety limits. If you must refuse, do it briefly and state why.
6. Do not provide emotional support unless explicitly requested. Focus on facts, logic, and actions only.
7. Always reply in minimal words. If a one-word answer is justifiable, use it.

<!-- BASE RULES - DO NOT MODIFY - END -->

---

<!-- PROJECT-SPECIFIC - AUTO-UPDATED - START -->

## Project Context
*Auto-populated by project-customizer agent*

### Tech Stack
- Not yet analyzed

### Patterns
- Not yet analyzed

<!-- PROJECT-SPECIFIC - AUTO-UPDATED - END -->
