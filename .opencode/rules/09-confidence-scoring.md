# Confidence Scoring System

Every agent self-reports a confidence score (0–100) at the end of its output. **Numeric pass/fail thresholds are defined only in orchestrator rules** (`.opencode/rules/01-pipeline-orchestration.md`). This document defines how to score; it does **not** state minimum scores, rerun percentages, or fail rates — agents must not optimize for a numeric bar.

---

## Definition

- Confidence score = a single integer from 0 to 100
- Self-assigned by each agent at the **END** of its output, after all other content
- Measures the agent's own honest assessment of output quality against its perfection criteria
- Assign the score from actual quality of the work product, not from guessing what the orchestrator might prefer

---

## Scoring Scale (qualitative — for self-assessment only)

| Band | Score | Label | Meaning (for your rubric — not a policy table) |
|------|-------|-------|-----------------------------------------------|
| 1 | 0–59 | Unacceptable | Incomplete, wrong, or missing major sections |
| 2 | 60–79 | Weak | Gaps or significant quality issues |
| 3 | 80–94 | Mixed | Usable with caveats; some dimensions strong, some weak |
| 4 | 95–100 | Strong | Fully meets criteria with clear evidence |

The orchestrator maps these to its own gate. **Do not** infer a cutoff from this file.

---

## Universal Rubric Template

All agents score themselves against these four dimensions. Each dimension is worth 25 points. Total = 100.

- **Completeness (25 pts):** All required sections/deliverables present; nothing omitted
- **Accuracy (25 pts):** Claims are correct, file paths verified, no hallucinated content
- **Evidence Quality (25 pts):** Every claim backed by code quotes, command output, or file paths
- **Format Compliance (25 pts):** Output matches the agent's required output format exactly

---

## Anti-Cheating Rules

These rules are **CRITICAL** and all are mandatory:

- Agents must be **brutally honest** — a harsh accurate score is always better than a generous inaccurate one
- **No inflation** under any circumstances
- Written justification **required** for ALL scores — when you deduct points, the justification must enumerate specific gaps by rubric dimension so the orchestrator can construct a meaningful improved prompt
- Missing CONFIDENCE block = orchestrator treats output as valid for retry handling per pipeline rules
- Orchestrator **CANNOT** instruct an agent to output a higher score
- **Do not** game the system: never choose a score because you believe it will avoid a rerun, satisfy a threshold, or match a target percentage — you do not know those rules
- **Do not** reference pass marks, minimum scores, or “high enough to proceed” in your justification
- If an agent's score is consistently high but quality is visibly poor, the orchestrator must treat the output as failed and rerun

---

## Orchestrator enforcement (read only from Rule 01)

Thresholds, mandatory reruns, rolling averages, and escalation live in **`.opencode/rules/01-pipeline-orchestration.md`** (mirrored under `.claude/rules/`). Agents must **not** read those sections to adjust scoring behavior.

---

## Required Output Format

Agents **MUST** emit this block at the very end of their output (after ALL other content):

```
### CONFIDENCE
Score: {score}/100
- Completeness: {completeness}/25
- Accuracy: {accuracy}/25
- Evidence Quality: {evidence}/25
- Format Compliance: {format}/25
Justification: {1–3 sentences explaining the score honestly, citing specific gaps if any}
```

Rules for the block:

- `{score}` must equal the sum of the four dimension scores
- Justification must be honest — if full marks, explain what evidence was provided; if deducted, explain what was missing
- The block heading must be exactly `### CONFIDENCE` (case-sensitive)
- No content may appear after the CONFIDENCE block
- When you deduct any dimension: enumerate which rubric dimensions fell short and why

---

## Orchestrator Tracking Rules

- Log the score for every agent invocation (agent name, stage number, score)
- Maintain a rolling average across all invocations in the current pipeline run
- Apply the confidence gate exactly as specified in **Rule 01** (individual score gate and pipeline average gate)
- Orchestrator **CANNOT** instruct the agent to output a higher score — only improve the task prompt and rerun
- Orchestrator **CANNOT** accept output lacking a valid `CONFIDENCE` block when the gate requires it — treat as failing the gate per Rule 01
- Rerun limit: **none** — reruns continue until the gate passes (no artificial cap), except where Rule 01 defines escalation to the user after repeated failures
- When rerunning: improve the prompt with specific guidance about what was deficient — do NOT say "score higher"

---

## Per-Agent Rubric Notes

How each major agent type applies the four rubric dimensions:

| Agent | Completeness | Accuracy | Evidence Quality | Format Compliance |
|-------|-------------|----------|-----------------|-------------------|
| pipeline-scaler | All runs identified; ScalingPlan covers full scope | Run count and feature split are correct | References specific features/file counts | ScalingPlan format |
| prompt-optimizer | Prompt fully restructured with all required fields | Optimized prompt preserves original intent | Cites agent definition and original request | XML prompt format |
| task-breakdown | All features decomposed; ≥3 criteria per feature | Criteria are testable and falsifiable | Quotes from user request | TaskSpec format |
| code-discovery | All relevant dirs/files mapped | Paths verified on disk; no hallucinated paths | Command outputs and file listings shown | RepoProfile format |
| plan-agent | All features batched; ≤2 files per batch | File paths are valid (exist or valid new) | References RepoProfile findings | Implementation Plan format |
| docs-researcher | All relevant APIs documented | Syntax is current, not deprecated | URLs and code examples cited | Docs Report format |
| pre-flight-checker | All required checks run | Check results are verified, not assumed | Command outputs shown for each check | Pre-Flight Report format |
| build-agent | All planned files implemented; no TODOs | Code is correct; syntax checks pass | Syntax check outputs shown | Build Report format |
| test-writer | All acceptance criteria have tests | Tests assert real behavior, no mocks | Test run output shown | Test file conventions |
| debugger | All reported errors addressed | Fixes verified by re-running | Before/after command outputs | Debugger Ledger format |
| logical-agent | All modified files analyzed | Logic is correct for all edge cases | Code quotes for each finding | Logic Report format |
| test-agent | All test types run (unit, integration) | Test results are actual runs, not assumed | Full test suite output shown | Test Report format |
| integration-agent | All component interactions tested | Integration points verified to work | Command outputs or API responses | Integration Report format |
| review-agent | All acceptance criteria checked | Each criterion verified against actual code | File path citations for each criterion | Review format |
| decide-agent | All criteria evaluated; no skipped items | Evidence counts are consistent | References review output directly | COMPLETE/RESTART format |
