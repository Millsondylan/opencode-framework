#!/usr/bin/env bash
# add-confidence-to-agents.sh
# Appends the mandatory CONFIDENCE scoring section to every agent .md file
# in .opencode/agents/ then syncs to .claude/agents/ (preserving README.md).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

OPENCODE_AGENTS="${REPO_ROOT}/.opencode/agents"
CLAUDE_AGENTS="${REPO_ROOT}/.claude/agents"

MARKER="## Mandatory: Confidence Scoring"

# The exact text to append.
# read -r -d '' returns exit code 1 when it hits EOF, which is normal.
# We use || true to prevent set -e from aborting.
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
- For scores below 85: enumerate specific gaps by rubric dimension
- **NEVER inflate your score** — brutal honesty is required
- The orchestrator **cannot** tell you to score higher
- See `.opencode/rules/09-confidence-scoring.md` for full details
ENDOFTEXT

echo "=== Adding CONFIDENCE section to .opencode/agents/ ==="

added=0
skipped=0

for filepath in "${OPENCODE_AGENTS}"/*.md; do
    filename="$(basename "${filepath}")"

    if grep -qF "${MARKER}" "${filepath}"; then
        echo "  SKIP (already present): ${filename}"
        (( skipped++ )) || true
        continue
    fi

    # Append the section (printf preserves the leading newline in the heredoc)
    printf '%s' "${CONFIDENCE_SECTION}" >> "${filepath}"
    echo "  ADDED: ${filename}"
    (( added++ )) || true
done

echo ""
echo "Done: ${added} files updated, ${skipped} files skipped."

echo ""
echo "=== Syncing .opencode/agents/ → .claude/agents/ (preserving README.md) ==="

# rsync: copy all .md files from opencode to claude, but do NOT delete extras
# (so README.md in .claude/agents/ is preserved).
rsync -av --include="*.md" --exclude="*" \
    "${OPENCODE_AGENTS}/" "${CLAUDE_AGENTS}/"

echo ""
echo "=== Verification ==="

opencode_count=$(grep -rl "${MARKER}" "${OPENCODE_AGENTS}"/*.md | wc -l | tr -d ' ')
claude_count=$(grep -rl "${MARKER}" "${CLAUDE_AGENTS}"/*.md | wc -l | tr -d ' ')
total_opencode=$(ls "${OPENCODE_AGENTS}"/*.md | wc -l | tr -d ' ')
total_claude=$(ls "${CLAUDE_AGENTS}"/*.md | wc -l | tr -d ' ')
readme_check=$(test -f "${CLAUDE_AGENTS}/README.md" && echo "EXISTS" || echo "MISSING")

echo "  .opencode/agents/ : ${opencode_count}/${total_opencode} files have CONFIDENCE section"
echo "  .claude/agents/   : ${claude_count}/${total_claude} files have CONFIDENCE section"
echo "  README.md in .claude/agents/: ${readme_check}"

if [[ "${opencode_count}" -eq "${total_opencode}" ]]; then
    echo "  PASS: All .opencode agent files updated."
else
    echo "  WARN: $(( total_opencode - opencode_count )) .opencode agent file(s) still missing the section."
fi

if [[ "${readme_check}" == "EXISTS" ]]; then
    echo "  PASS: README.md preserved."
else
    echo "  FAIL: README.md was deleted!"
    exit 1
fi
