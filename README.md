# Claude Code multi-agent framework

A **production-grade multi-agent system** for software development in **Claude Code**. This repository holds `.claude/agents/`, `.claude/rules/`, skills, and orchestration docs (`CLAUDE.md`, `AGENTS.md`). Instead of one model doing everything, specialized subagents run in a strict pipeline to build, test, and review code with engineering discipline.

> **Core idea:** The orchestrator dispatches subagents via the Task tool, agents execute with fixed roles, quality gates apply, and the pipeline continues until `decide-agent` completes.

---

## What makes this different

| Traditional chat | This framework |
|------------------|----------------|
| One session does everything | Many specialized agents |
| Easy to skip steps | Sequential pipeline, documented stages |
| Inconsistent quality | Review, tests, and logic checks built in |

---

## The pipeline (stages 1–16)

Every engineering request flows through the stages in `CLAUDE.md` / `AGENTS.md`:

```
Stage 1:  pipeline-scaler      → Scaling plan
Stage 2:  prompt-optimizer     → Optimized prompt for task-breakdown
Stage 3:  task-breakdown       → TaskSpec
Stage 4:  [user confirmation]  → Approve plan (only orchestrator pause)
Stage 5:  code-discovery       → RepoProfile
Stage 6:  plan-agent           → Implementation plan
Stage 7:  docs-researcher      → Library docs
Stage 8:  pre-flight-checker   → Preconditions
Stage 9:  build-agent-N        → Implement (1–2 files per agent, chain 1→55→1)
Stage 10: test-writer          → Tests
Stage 11: debugger             → Fix errors (debugger → … → debugger-11)
Stage 12: logical-agent        → Logic review
Stage 13: test-agent           → Run tests
Stage 14: integration-agent    → Integration checks
Stage 15: review-agent         → Review vs acceptance criteria
Stage 16: decide-agent         → COMPLETE or RESTART
```

**Browser / live-site work** uses `claude-in-chrome` as documented in `CLAUDE.md` (not part of this numbered table).

---

## Models (Claude Code)

Agent definitions in `.claude/agents/*.md` set `model` in frontmatter. Project policy (see `CLAUDE.md`):

| Role | Typical `model` |
|------|------------------|
| **plan-agent**, all **build-agent** roles (including numbered), **debugger** … **debugger-11** | `opus` |
| **code-discovery**, **decide-agent**, **perfection-validator**, most other pipeline agents | `sonnet` |

Do not override `model` from `Task` calls; it comes from each agent file.

---

## Debugger chain (11 agents)

```
debugger → debugger-2 → … → debugger-11
```

Each step tries fixes and passes remaining work on failure.

---

## Build-agent chain (55 agents)

`build-agent-1` through `build-agent-55` (and `build-agent`) implement small batches (typically 1–2 files), cycling until the plan is done.

---

## What the orchestrator must not do

- **No direct code edits** — dispatch `build-agent-N` (and other agents) instead.
- **No skipping** `pipeline-scaler` for repo work.
- **No parallel** agent dispatches.
- **No stopping** between stages except user confirmation after task-breakdown.

---

## Repository layout (Claude Code)

```
├── CLAUDE.md              # Orchestrator + pipeline (canonical for this repo)
├── AGENTS.md              # Same rules, Cursor-oriented framing
├── .ai/README.md          # ACM / safety for agents
├── .claude/
│   ├── agents/            # Subagent definitions (YAML frontmatter + body)
│   ├── rules/             # Pipeline rules (01–09, …)
│   ├── skills/            # Domain SKILL.md files
│   └── settings.json      # Hooks (optional)
└── scripts/               # Helper scripts (e.g. confidence section)
```

---

## Usage example

**Request:** “Add user authentication to my app.”

The pipeline runs from `pipeline-scaler` through `decide-agent` as in the table above. You confirm once after `task-breakdown`; later stages auto-continue until `COMPLETE` or `RESTART`.

---

## Philosophy

This treats AI-assisted work as a **structured engineering process**: specialization, explicit stages, tests, and reviews—not a single chat that tries to do everything at once.

---

*Built for Claude Code. Run the pipeline, trust the process, ship quality code.*
