# OpenCode: Subagents Must Not Re-Delegate

**SCOPE:** Loaded only for **OpenCode** via `.opencode/opencode.json` `instructions`. Subagents must not treat this as optional guidance—it overrides any urge to “run the pipeline from here.”

## What this rule means

When your agent definition has `mode: subagent` (or you were invoked as a subagent/tool Agent):

1. **No re-delegation.** You MUST NOT use the **Task** tool, **Agent** tool, or any equivalent that **spawns another subagent** or pipeline agent (e.g. `pipeline-scaler`, `task-breakdown`, `build-agent-*`, `debugger`, etc.).
2. **No subagent chains.** Subagent A → Subagent B is **forbidden**. Only the **top-level orchestrator session** may dispatch the next agent.
3. **If you need someone else’s stage**, output **one line of plain text** only:  
   `REQUEST: <agent-name> — <short reason>`  
   and **STOP**. Do not call Task yourself.
4. **Do your single job** using only the tools your definition allows (Read, Edit, Write, Bash, Grep, Glob, MCP, etc.). Never “continue the pipeline” by dispatching.

## Why

Nested Task/Agent calls from inside a subagent duplicate orchestration, burn tokens, and break the **one dispatch per orchestrator turn** contract. OpenCode expects the **main** session to route all stages.

## If your tool list includes Task

**Ignore Task** while running as a subagent unless the product explicitly marks you as the orchestrator (main session). When in doubt: no Task, no Agent spawn—REQUEST line only.
