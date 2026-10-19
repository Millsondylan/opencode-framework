# OpenCode Skill Test Prompts

Minimal prompts to exercise skills and verify build-agent activation.

## Quick Start

1. **Run a skill test:** Use one of the test prompts below with the appropriate agent
2. **Verify build-agent activation:** Use the verification procedure in `VERIFICATION-PROCEDURE.md`

## Test Prompts

| File | Skill | Category | Purpose |
|------|-------|----------|---------|
| `test-auth-schema.md` | auth-schema | Domain chain | Produces auth schema artifacts (User, AuthToken, Role) |
| `test-architecture-agent.md` | architecture-agent | Architecture | Produces architecture structure (Clean Architecture, feature-first) |
| `test-test-writer.md` | test-writer | Quality | Produces test plan or test file with real assertions |
| `verify-build-agent-skill.md` | auth-schema | Verification | Verifies build-agent reads SKILL.md and follows guidance |

## How to Run

### Option A: Via Orchestrator (Task Tool)

1. **Orchestrator** reads the prompt file
2. **Orchestrator** dispatches to build-agent-1 (or test-writer) with the prompt content
3. **Include** `skill: {name}` in the prompt when testing skill activation
4. **Evaluate** output against the "Expected Verifiable Output" in each prompt file

### Option B: Direct Agent Invocation

If you invoke agents directly (e.g., via Cursor Composer or a custom runner):

1. **Load** the prompt from `.opencode/prompts/test-{skill}.md`
2. **Append** `skill: {name}` to the prompt for build-agent tests
3. **Dispatch** to the target agent
4. **Check** output for skill-specific artifacts

### Option C: Verification Test Only

To verify build-agent skill activation:

1. **Read** `.opencode/prompts/verify-build-agent-skill.md`
2. **Use** the "Verification Prompt" section
3. **Dispatch** to build-agent-1 via the task tool
4. **Complete** the checklist in the same file

## Verification Procedure

See [VERIFICATION-PROCEDURE.md](./VERIFICATION-PROCEDURE.md) for the full step-by-step procedure to verify that build-agent-1 reads `.opencode/skills/auth-schema/SKILL.md` when `skill: auth-schema` is assigned.

**Quick run:** Execute the verification script to validate setup and print instructions:

```bash
./.opencode/prompts/run-verification.sh
```

## Minimal Footprint

- One prompt per category (domain, architecture, quality)
- Verification prompt focuses on auth-schema only
- No need to test all 126+ skills; these are representative

## Output Location

Test outputs are produced by the agent. For report-style outputs, the agent may write to a file or return the content in its response. Check the agent's output for the artifact location.
