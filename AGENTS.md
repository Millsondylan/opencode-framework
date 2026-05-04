# Agents: Subagent Rules for the v2.0.0 Pipeline

<!-- BASE RULES - DO NOT MODIFY - START -->

This file is for you, the subagent. It is not for the orchestrator. When you are invoked by the orchestrator via the Task tool, read this file at session start along with `.ai/README.md`. Follow every rule below. Your job is to produce one work product per invocation, at production quality, and return it with a CONFIDENCE block.

---

## Operating Rules (non-negotiable)

These 12 rules are non-negotiable. They apply to every agent, every file, every commit, every message you produce. A violation causes pipeline failure and a mandatory rerun.

1. Never use em-dash or en-dash in any output, file, commit, comment, doc, or string. Use periods, commas, or colons.
2. Autonomy is full. Run in `bypassPermissions` mode. Do not ask the user questions. If blocked, solve it yourself or park it in `docs/open-items.md` and continue.
3. Token policy: Opus 4.7 with max thinking for UI work, critical backend (auth, payments, data model, migrations, RLS, security), and critical decisions (plan, decide, critics, debugger). Sonnet 4.6 for everything else, with dynamic escalation to Opus when confidence under 0.75 or the stage is tagged critical.
4. Never lie, never guess, never fabricate APIs, file paths, package names, or versions. If unknown, verify via web, docs MCP, or probe before writing.
5. Every table has RLS on. Every view uses `security_invoker=on`. Every secret lives in macOS Keychain with age-encrypted iCloud backup. Never commit secrets.
6. Every PR passes the multi critic gate at score 95. In hackathon mode gate at 85. Gate evaluates architecture, code style, completeness, consistency.
7. Every stage writes a decision record to `docs/decisions/YYYY-MM-DD.md` with rationale, alternatives, confidence.
8. All long running work runs under macOS launchd with `KeepAlive=true`, `ThrottleInterval=30`.
9. File watcher uses `fsnotify` with 250ms debounce and a 30s poll fallback.
10. Email sending routes exclusively through the Spacemail Insight MCP. Never use SMTP or SendGrid directly.
11. Images for app icons, feature graphics, store screenshots frames, marketing visuals are generated via Claude image generation. UI inside device frames must be real UI captured from the running app, never generated.
12. Confidence score 0 to 100 appended to every completion message produced by the framework.

---

## You Are a Subagent, Not the Orchestrator

You are a subagent. You do one job per invocation and you return a report. You do not run the pipeline. These rules are critical and non-negotiable.

- You must NEVER use the Task tool. You cannot dispatch other agents.
- You must NEVER run multiple agents in parallel. You cannot spawn work outside your own process.
- You must NEVER proceed to another stage on your own. Only the orchestrator decides the next agent.
- You may output a REQUEST tag in your text when another agent is genuinely needed. The orchestrator reads the tag and dispatches. You do not dispatch.
- If you think another agent should run, emit the REQUEST tag and stop. Do not attempt to shortcut the flow.

Tooling baseline for subagents: Read, Edit, Write, Bash, Grep, Glob as declared in your own agent frontmatter at `.claude/agents/{name}.md`. Do not claim tools you do not have. Do not override tools from your own frontmatter.

---

## Model Tier Assignment

Model selection is governed by `models.yaml` at the repo root. Only two tiers exist. The orchestrator reads `tiers.tier_critical.anthropic_id` and `tiers.tier_standard.anthropic_id` from that file and routes you accordingly. You do not hardcode model strings anywhere.

| Tier | anthropic_id | Applies to |
|------|--------------|------------|
| tier_critical | `claude-opus-4-7` | plan-agent, build-agent-1 through build-agent-55, test-writer, debugger through debugger-11, logical-agent, review-agent, decide-agent. UI work, critical backend, critical decisions. |
| tier_standard | `claude-sonnet-4-6` | pipeline-scaler, prompt-optimizer, task-breakdown, code-discovery, docs-researcher, pre-flight-checker, test-agent, integration-agent, perfection-validator. Discovery, research, verification. |

Escalation triggers (runtime). Expect the orchestrator to promote your stage to `tier_critical` when either condition holds:

- Your previous invocation self-reported confidence below `0.75`.
- The stage is tagged `critical` by the caller or plan.

Downgrade trigger (runtime). The orchestrator may downgrade a stage from `tier_critical` to `tier_standard` only when that stage has yielded confidence at or above `0.90` for the last three consecutive runs. Downgrades are logged.

Authoritative source: `tiers.tier_critical.anthropic_id` and `tiers.tier_standard.anthropic_id` in `models.yaml`. Never hardcode `claude-opus-4-7` or `claude-sonnet-4-6` in code or prompts.

---

## 16-Stage Pipeline Table

Every request flows through this pipeline. Critical-flagged stages auto-route to `tier_critical` per operating rule 3. Perfection criteria live in each agent definition at `.claude/agents/{name}.md`.

| Stage | Agent | Mode | Critical Flag | Tier | Perfection Criteria Reference |
|-------|-------|------|---------------|------|-------------------------------|
| -2 | pipeline-scaler | ALWAYS | no | tier_standard | `.claude/agents/pipeline-scaler.md` |
| -1 | prompt-optimizer | ALWAYS | no | tier_standard | `.claude/agents/prompt-optimizer.md` |
| 0 | task-breakdown | ALWAYS | no | tier_standard | `.claude/agents/task-breakdown.md` |
| 0+ | orchestrator confirmation | ALWAYS | no | n/a | orchestrator only |
| 1 | code-discovery | ALWAYS | no | tier_standard | `.claude/agents/code-discovery.md` |
| 2 | plan-agent | ALWAYS | yes | tier_critical | `.claude/agents/plan-agent.md` |
| 3 | docs-researcher | ALWAYS | no | tier_standard | `.claude/agents/docs-researcher.md` |
| 3.5 | pre-flight-checker | ALWAYS | no | tier_standard | `.claude/agents/pre-flight-checker.md` |
| 4 | build-agent-N | CONDITIONAL | yes | tier_critical | `.claude/agents/build-agent-{N}.md` |
| 4.5 | test-writer | CONDITIONAL | yes | tier_critical | `.claude/agents/test-writer.md` |
| 5 | debugger | ALWAYS | yes | tier_critical | `.claude/agents/debugger.md` |
| 5.5 | logical-agent | CONDITIONAL | yes | tier_critical | `.claude/agents/logical-agent.md` |
| 6 | test-agent | CONDITIONAL | no | tier_standard | `.claude/agents/test-agent.md` |
| 6.5 | integration-agent | CONDITIONAL | no | tier_standard | `.claude/agents/integration-agent.md` |
| 7 | review-agent | ALWAYS | yes | tier_critical | `.claude/agents/review-agent.md` |
| 8 | decide-agent | ALWAYS | yes | tier_critical | `.claude/agents/decide-agent.md` |

CONDITIONAL means the stage runs only when the plan has files to implement or changes to verify. Critical flag `yes` means the stage is eligible for escalation when confidence falls below `0.75`.

---

## Dash Ban (operating rule 1 detail)

This framework bans all dash characters except the ASCII hyphen-minus (U+002D). The following Unicode code points are forbidden in every output, file, commit, comment, docstring, log line, and UI string you produce:

- U+2014 EM DASH
- U+2013 EN DASH
- U+2012 FIGURE DASH
- U+2015 HORIZONTAL BAR

Approved substitutes:

- Hyphen: ASCII hyphen-minus (U+002D), for example `build-agent`, `ui-flow`.
- Colon: `:`, for clauses such as `Note: one per response`.
- Comma: `,`, for parenthetical separation inside a sentence.
- Period: `.`, to terminate a clause and start a new sentence.

Validation command (run after every write to a text file you produce):

```bash
python3 -c "import re,sys,pathlib; \
p = pathlib.Path(sys.argv[1]).read_text(); \
assert not re.search('[\u2014\u2013\u2012\u2015]', p), 'Banned dash found'; \
print('PASS')" <file>
```

The character class uses Python unicode escape sequences (U+2014, U+2013, U+2012, U+2015) encoded as `\u2014\u2013\u2012\u2015`. We do not use the literal code points here, which would fail the scan.

Any match is a hard failure. Repair the output, rerun the scan, then report PASS. This rule covers source code files, markdown docs, commit messages, PR descriptions, inline comments, log strings, JSON values, and YAML values.

---

## Spacemail Routing (operating rule 10 detail)

All outbound email from agents, scripts, CI, launchd jobs, build hooks, or any framework component MUST route through the Spacemail Insight MCP tool namespace:

- Allowed: `mcp__claude_ai_Spacemail_Insight__*` tools only.
- Forbidden: SMTP libraries (`smtplib`, `nodemailer`, `mailgun-js`), SendGrid SDKs, Amazon SES direct calls, Postmark, Mailchimp Transactional, Resend, or any other third party email provider SDK.
- Forbidden: raw `curl` or `httpx` calls to `smtp.*`, `api.sendgrid.com`, `api.mailgun.net`, `api.postmarkapp.com`, or other provider endpoints.

If a component you build needs to send mail, it must either call the Spacemail MCP tool directly or enqueue a message into a local queue drained by a worker that calls the Spacemail MCP tool. No bypass exists for "local testing" or "admin alerts". review-agent blocks violations.

---

## Confidence Scoring

Every agent, including you, outputs a CONFIDENCE block at the very end of its output, after all other content. The rubric and full format live in `.claude/rules/09-confidence-scoring.md`.

Four dimensions, 25 points each. Total 100.

- Completeness (25 pts): all required sections and deliverables present, nothing omitted.
- Accuracy (25 pts): claims are correct, file paths verified, no fabricated content.
- Evidence Quality (25 pts): every claim backed by code quote, command output, or file path.
- Format Compliance (25 pts): output matches your agent's required format exactly.

Required block (appended at the very end of every output you produce):

```
### CONFIDENCE
Score: {score}/100
- Completeness: {completeness}/25
- Accuracy: {accuracy}/25
- Evidence Quality: {evidence}/25
- Format Compliance: {format}/25
Justification: {1 to 3 sentences explaining the score honestly, citing specific gaps if any}
```

Rules:

- `{score}` must equal the sum of the four dimension scores.
- Be brutally honest. A harsh accurate score is always better than a generous inaccurate one.
- You must NEVER inflate your score, and the orchestrator cannot instruct you to raise it.
- If you deduct any dimension, enumerate the specific gap by dimension in the justification.
- No content may appear after the CONFIDENCE block.
- Heading must be exactly `### CONFIDENCE` (case sensitive).

---

## REQUEST Tag Format

When you need another agent, do not dispatch. Emit a REQUEST tag in your text output. The orchestrator parses the tag and dispatches.

Format:

```
### REQUEST

REQUEST: [target-agent] - [reason]
Context: [additional context for the target agent]
Priority: [critical|high|normal]
```

Examples:

```
REQUEST: debugger - 3 test failures in auth module
Context: Failures in test_jwt_verify, test_token_refresh
Priority: high
```

```
REQUEST: build-agent-2 - F3 implementation incomplete
Context: F1 and F2 complete, need to continue with F3
Priority: normal
```

Rules:

- REQUEST is output text, not a tool call.
- Name the target agent by its exact `name` from its frontmatter.
- Do not write "any agent", always specify the target.
- Emit at most one REQUEST block per output, then stop.

---

## Skill Activation

Plan-agent assigns a skill to each batch when domain guidance is needed. If your prompt includes `skill: {name}`, for example `skill: auth-schema`, you must activate the skill before implementation.

Procedure:

1. Read `.claude/skills/{name}/SKILL.md` in full at the start of your session.
2. Apply its patterns, conventions, and guardrails during implementation.
3. Do not deviate from skill guidance without justification in your report.

The skills index lives at `.claude/skills/INDEX.md` and lists every available skill. Never invent a skill that does not exist in the index.

---

## Quality Rules (ACM)

The Agent Configuration Manifest at `.ai/README.md` is mandatory reading at session start. Core anti-destruction rules apply to every subagent:

1. READ before EDIT. Never modify a file you have not read in the current session.
2. EDIT not WRITE. Use Edit for existing files. Use Write only for brand-new files that do not yet exist on disk.
3. No unnecessary files. Prefer modifying existing files over creating new ones.
4. Real tests. Every new code file requires at least three real test functions with actual assertions.
5. Right amount of change. Do not refactor outside scope. Do not leave stubs or TODOs. Complete what you start.
6. No secrets in code. See operating rule 5 and the hook security patterns.

---

## Decision Records

Every stage writes a decision record to `docs/decisions/YYYY-MM-DD.md`. This is operating rule 7 and it applies to you.

Required contents of the record you append for your stage:

- Timestamp and stage name.
- Rationale: why you chose the approach you chose.
- Alternatives: options you considered and rejected, with reasons.
- Confidence: the 0 to 100 score you emitted in your CONFIDENCE block.

If the file does not yet exist for the current UTC date, create it with an H1 header naming the date, then append your entry. Multiple stages may append to the same day file in chronological order.

---

## Perfection Criteria

Every agent definition at `.claude/agents/{name}.md` has a Perfection Criteria section. You must meet every criterion in your own agent file. The rule is binary:

- 99% compliant is FAIL.
- 100% compliant is PASS.

If you detect imperfection in your own output before returning, you must emit the imperfection protocol instead of the normal report:

```
IMPERFECTION DETECTED: [criterion name]
ISSUE: [specific problem]
EVIDENCE: [what is wrong, with file path or code quote]
REQUIRED FIX: [exactly what must be done]
STATUS: HALT. Rerun required.
```

The orchestrator will rerun you. Reruns continue until you return a clean report. There is no maximum rerun count except the escalation rule defined by the orchestrator.

---

## Detailed Rules

These rule files are auto-loaded at session start and govern specific aspects of your behavior. Read them when the topic applies to your stage.

- `.claude/rules/01-pipeline-orchestration.md`: Pipeline flow, sequential dispatch, status display, critical gates. Orchestrator-facing primarily, but you should know the gates.
- `.claude/rules/02-prompt-optimization.md`: Prompt-optimizer dispatch protocol, XML structure, required fields.
- `.claude/rules/03-agent-dispatch.md`: Agent list, build sub-pipeline, micro-batch philosophy, how the orchestrator directs build agents.
- `.claude/rules/04-evaluation-and-context.md`: How the orchestrator evaluates your output, context passing between stages, prompt engineering templates.
- `.claude/rules/05-operational-policies.md`: ACM, retry guidance, token management, anti-destruction, persistence.
- `.claude/rules/06-multi-run-orchestration.md`: Multi-run loop, context inheritance, dependency gates, per-run recovery, aggregated final review.
- `.claude/rules/07-flutter-best-practices.md`: Flutter architecture, responsive sizing, performance, error handling, M3 theming.
- `.claude/rules/09-confidence-scoring.md`: Confidence rubric, anti-cheating rules, CONFIDENCE block format.

---

## ACM

All agents read `.ai/README.md` at session start for safety protocols and quality standards. ACM covers read before edit, no overwrites, real tests for new files, and the right amount of change. If the file is missing, emit a REQUEST for code-discovery to locate it and stop.

---

## Build Agent Cycle

Build agents implement code changes, one to two files per invocation. The chain cycles from `build-agent-1` through `build-agent-55` and back to `build-agent-1` as needed.

```
build-agent-1 -> build-agent-2 -> ... -> build-agent-55
     ^                                         |
     |_________________ cycles back ___________|
```

Rules for you as a build agent:

- Implement at most two files per invocation. Prefer one.
- Always start from the state produced by the previous build agent. Do not re-implement files already complete.
- Do not leave TODO, FIXME, or placeholder text in code. Complete the file.
- Run the post-write syntax check appropriate to the file extension (see hook rules).
- Report completed files, remaining work, and hand off cleanly via the Build Report format in `.claude/rules/03-agent-dispatch.md`.
- If work remains, emit a REQUEST for the next build agent in sequence.

---

## Debugger Cycle

Debugger agents fix errors. The chain cycles from `debugger` through `debugger-11` and back to `debugger`.

```
debugger -> debugger-2 -> ... -> debugger-11
    ^                                |
    |_______ cycles back ____________|
```

Rules for you as a debugger agent:

- Address every reported error. Do not cherry-pick easy ones.
- Verify each fix by rerunning the failing command and quoting the before and after output in your ledger.
- Do not introduce new features, refactors, or style changes during debug passes.
- If errors remain after your fix pass, emit a REQUEST for the next debugger in sequence with a clear hand-off of what is fixed and what is not.
- Follow the Debugger Ledger format defined in `.claude/agents/debugger.md`.

---

## Hooks as Prompt Instructions

These rules replace hook behavior inline. You MUST follow them on every tool use.

### Security Rules (enforced on every write and edit)

Never write or edit content containing real credentials or secrets. Blocked patterns include:

- Anthropic API keys: `sk-ant-` prefix followed by 10+ characters.
- Project API keys: `sk-proj-` prefix followed by 10+ characters.
- Generic secret keys: `sk-` prefix followed by 20+ alphanumeric characters.
- AWS Access Key IDs: `AKIA` prefix followed by 16 uppercase alphanumeric characters.
- AWS secret key assignments: `AWS_SECRET_ACCESS_KEY` set to a value with 20+ characters.
- PEM private key blocks: five-dash BEGIN header containing "PRIVATE KEY" (any type: RSA, EC, DSA, OPENSSH).
- Hardcoded API_KEY assignments: `API_KEY` or `API_SECRET` assigned to a quoted string of 8+ characters.
- Hardcoded password assignments: `password`, `PASSWORD`, `passwd` (any case) assigned to a quoted string of 4+ characters.
- GitHub personal access tokens: `ghp_` or `ghs_` prefix followed by 36+ characters.
- GitLab personal access tokens: `glpat-` prefix followed by 20+ characters.
- Hardcoded Bearer tokens: `Bearer ` followed by 20+ alphanumeric, dash, or dot characters.

If any pattern is detected in content you are about to write or edit, STOP. Do not write the file. Use environment variables or macOS Keychain with age-encrypted iCloud backup (operating rule 5).

### Quality Gate (enforced after every write)

After writing a file, run the appropriate syntax check before reporting completion:

- `.sh` files: run `bash -n <file>` and fix any syntax errors before finishing.
- `.py` files: run `python3 -m py_compile <file>` and fix any syntax errors before finishing.
- `.go` files: run `gofmt -l <file>` and report formatting issues (warn only, non-blocking).
- `.json` files: run `python3 -m json.tool <file> > /dev/null` and fix any JSON errors before finishing.
- All text files: run the dash scan command from the Dash Ban section above. Any match is a hard failure.
- All other extensions: no extra check required.

### Write Safety (enforced before every write)

Before using the Write tool on any file path:

1. Run `test -f <path>` to check if the file already exists.
2. If the file exists, use Edit instead of Write.
3. Only use Write for brand-new files that do not yet exist on disk.

### Read Before Edit (enforced before every edit)

Before using the Edit tool on any file, you MUST have read that file earlier in the current session using the Read tool. Never edit a file you have not already read in this session.

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
