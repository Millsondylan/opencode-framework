---
name: graphify
description: Build and use a knowledge graph for a code/docs corpus, then answer via graph structure before raw file searching.
---

# /graphify - Knowledge Graph Workflow

Use this skill when a task needs fast architectural understanding across many files, docs, PDFs, screenshots, or mixed project artifacts.

## When to Use
- Large or unfamiliar repositories
- "How does this system connect?" questions
- Repeated architecture queries over time
- Mixed corpus analysis (code + docs + media)

## Core Rule
If `graphify-out/GRAPH_REPORT.md` exists, read it **before** broad raw-file search. Prefer graph-guided navigation over blind grep/glob sweeps.

## Install (official)
- Package: `pip install graphifyy` (official package name is `graphifyy`)
- Skill/setup for OpenCode: `graphify install` and optionally `graphify opencode install`

## Typical Flow
1. Build or refresh graph
   - `/graphify .`
   - `/graphify . --update`
2. Read summary first
   - `graphify-out/GRAPH_REPORT.md`
3. Drill into graph queries only as needed
   - `/graphify query "show the auth flow"`
4. Use resulting paths/files as focused context for implementation or review

## Output Artifacts
- `graphify-out/graph.html` (interactive graph)
- `graphify-out/GRAPH_REPORT.md` (high-level orientation)
- `graphify-out/graph.json` (queryable persistent graph)
- `graphify-out/cache/` (incremental updates)

## Safety and Accuracy
- Treat `EXTRACTED` edges as stronger than `INFERRED`
- Call out uncertainty when only inferred links are available
- Do not claim graph coverage if corpus has never been built

## Practical Integration in this repo
- For OpenCode workflows, keep this skill in `.opencode/skills/graphify/SKILL.md`
- For Claude parity, mirror into `.claude/skills/graphify/SKILL.md`
- Use this skill as an analysis accelerator before task planning on large codebases
