#!/usr/bin/env bash
# add-confidence-to-agents.sh
# Appends the mandatory CONFIDENCE scoring section to every agent .md file in `.claude/agents/`
# (preserving README.md — never delete it).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

CLAUDE_AGENTS="${REPO_ROOT}/.claude/agents"

MARKER="## Mandatory: Confidence Scoring"

read -r -d '' CONFIDENCE_SECTION << 'ENDOFTEXT' || true

---

## Mandatory: Confidence Scoring

**You MUST end every output with a CONFIDENCE block.** This is not optional. Missing it = score 0 and mandatory rerun.

```
### CONFIDENCE
Score: {score}/100
- Completeness: {completeness}/25
- Accuracy: {accuracy}/25
- Evidence Quality: {evidence}/25
- Format Compliance: {format}/25
Justification: {1-3 sentences}
```

**Rules:**
- Score yourself **honestly** — 99% correct = report 99, not 100
- The four dimension scores must sum to the total score
- Justification is **mandatory** for every score
- If you deducted any dimension points: enumerate specific gaps by rubric dimension
- **NEVER inflate your score** — brutal honesty is required
- The orchestrator **cannot** tell you to score higher
- See `.claude/rules/09-confidence-scoring.md` for full details
ENDOFTEXT

echo "=== Adding CONFIDENCE section to .claude/agents/ ==="

added=0
skipped=0

for filepath in "${CLAUDE_AGENTS}"/*.md; do
    filename="$(basename "${filepath}")"

    if grep -qF "${MARKER}" "${filepath}"; then
        echo "  SKIP (already present): ${filename}"
        (( skipped++ )) || true
        continue
    fi

    printf '%s' "${CONFIDENCE_SECTION}" >> "${filepath}"
    echo "  ADDED: ${filename}"
    (( added++ )) || true
done

echo ""
echo "Done: ${added} files updated, ${skipped} files skipped."

echo ""
echo "=== Verification ==="

claude_count=$(grep -rl "${MARKER}" "${CLAUDE_AGENTS}"/*.md 2>/dev/null | wc -l | tr -d ' ')
total_claude=$(ls "${CLAUDE_AGENTS}"/*.md | wc -l | tr -d ' ')
readme_check=$(test -f "${CLAUDE_AGENTS}/README.md" && echo "EXISTS" || echo "MISSING")

echo "  .claude/agents/   : ${claude_count}/${total_claude} files have CONFIDENCE section"
echo "  README.md in .claude/agents/: ${readme_check}"

if [[ "${readme_check}" == "EXISTS" ]]; then
    echo "  PASS: README.md present."
else
    echo "  WARN: README.md missing (optional)."
fi
