# Confidence Scoring System

Every agent self-reports a confidence score (0–100) at the end of its output. The orchestrator enforces thresholds: rerun any agent below 85, flag the pipeline if cumulative average drops below 95.

---

## Definition

- Confidence score = a single integer from 0 to 100
- Self-assigned by each agent at the **END** of its output, after all other content
- Measures the agent's own honest assessment of output quality against its perfection criteria
- The score must be assigned **BEFORE** the agent knows if it will be rerun — based on actual quality, not desired outcome

---

## Scoring Scale

| Band | Score | Label | Pipeline Consequence |
|------|-------|-------|---------------------|
| 1 | 0–59 | Unacceptable | Mandatory rerun; output is incomplete, wrong, or missing major sections |
| 2 | 60–84 | Below Threshold | Mandatory rerun; output has gaps or significant quality issues |
| 3 | 85–94 | Acceptable | Log warning and proceed; minor caveats noted |
| 4 | 95–100 | Pipeline-Safe | Proceed normally; output fully meets all criteria with evidence |

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
- Written justification **required** for ALL scores — for scores below 85, the justification must enumerate the specific gaps by rubric dimension so the orchestrator can construct a meaningful improved prompt
- Missing CONFIDENCE block = automatic score of **0** and mandatory rerun
- Orchestrator **CANNOT** instruct an agent to output a higher score
- Agents **CANNOT** reference the threshold to game the system (e.g., "I need 85 so I will say 85")
- If an agent's score is consistently high but quality is visibly poor, the orchestrator must treat the score as 0 and rerun

---

## Thresholds

Two enforcement levels:

- **Individual agent:** score < 85 → mandatory rerun with improved prompt before dispatching next stage
- **Pipeline-level:** if cumulative rolling average across all agent invocations in the current run drops below 95 → orchestrator logs a pipeline-level warning and reviews which stages are dragging the average

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

---

## Orchestrator Tracking Rules

- Log the score for every agent invocation (agent name, stage number, score)
- Maintain a rolling average across all invocations in the current pipeline run
- **Trigger rerun when:** individual score < 85 OR CONFIDENCE block is absent
- **Flag pipeline when:** rolling average < 95
- Orchestrator **CANNOT** instruct the agent to output a higher score — only improve the task prompt and rerun
- Orchestrator **CANNOT** accept output lacking a CONFIDENCE block — treat as score 0
- Rerun limit: **none** — reruns continue until score ≥ 85 (no artificial cap)
- **Escalation after 5 consecutive reruns below 85:** If the same agent scores below 85 on 5 consecutive attempts, the orchestrator must pause, log a diagnostic summary of all 5 scores and justifications, and surface the issue to the user rather than continuing to loop. This is the only defined exit from the rerun loop other than reaching ≥ 85.
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
