#!/bin/bash
# Verification tests for confidence scoring rule files (Claude Code — `.claude/rules/` only).
#
# Run: bash .claude/hooks/tests/test_confidence_scoring_rules.sh
# Or via: bash .claude/hooks/tests/run_all_tests.sh

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

CLAUDE_CS="$PROJECT_ROOT/.claude/rules/09-confidence-scoring.md"
CLAUDE_PO="$PROJECT_ROOT/.claude/rules/01-pipeline-orchestration.md"

PASSED=0
FAILED=0

pass() {
    echo -e "${GREEN}PASS${NC}: $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}FAIL${NC}: $1"
    FAILED=$((FAILED + 1))
}

check_contains() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if grep -qF "$pattern" "$file" 2>/dev/null; then
        pass "$label"
    else
        fail "$label"
    fi
}

echo "=========================================="
echo "Confidence Scoring Rules - Verification"
echo "=========================================="
echo ""

# -------------------------------------------------------
# Tests 1-2: File existence
# -------------------------------------------------------
echo "--- File existence ---"

if [ -f "$CLAUDE_CS" ]; then
    pass "Test 1: .claude/rules/09-confidence-scoring.md exists"
else
    fail "Test 1: .claude/rules/09-confidence-scoring.md exists"
fi

if [ -f "$CLAUDE_PO" ]; then
    pass "Test 2: .claude/rules/01-pipeline-orchestration.md exists"
else
    fail "Test 2: .claude/rules/01-pipeline-orchestration.md exists"
fi

echo ""

# -------------------------------------------------------
# Tests 4-13: Content checks on 09-confidence-scoring.md
# -------------------------------------------------------
echo "--- 09-confidence-scoring.md content ---"

check_contains "$CLAUDE_CS" \
    "# Confidence Scoring System" \
    "Test 4: Contains '# Confidence Scoring System' heading"

check_contains "$CLAUDE_CS" \
    "0–59" \
    "Test 5a: Scoring table band 0-59 present"

check_contains "$CLAUDE_CS" \
    "60–79" \
    "Test 5b: Scoring table band 60-79 present"

check_contains "$CLAUDE_CS" \
    "80–94" \
    "Test 5c: Scoring table band 80-94 present"

check_contains "$CLAUDE_CS" \
    "95–100" \
    "Test 5d: Scoring table band 95-100 present"

check_contains "$CLAUDE_CS" \
    "Universal Rubric Template" \
    "Test 6: Contains 'Universal Rubric Template' section"

check_contains "$CLAUDE_CS" \
    "{score}" \
    "Test 7: Contains '{score}' placeholder token in CONFIDENCE block template"

check_contains "$CLAUDE_CS" \
    "{completeness}" \
    "Test 8: Contains '{completeness}' placeholder token"

check_contains "$CLAUDE_CS" \
    "Anti-Cheating" \
    "Test 9: Contains 'Anti-Cheating' section"

check_contains "$CLAUDE_PO" \
    "below 90" \
    "Test 10: Rule 01 contains individual gate 'below 90' (agent rubric must not embed this number)"

check_contains "$CLAUDE_PO" \
    "below 95" \
    "Test 11: Rule 01 contains pipeline rolling average 'below 95' flag"

check_contains "$CLAUDE_CS" \
    "### CONFIDENCE" \
    "Test 12: Contains '### CONFIDENCE' heading (required output block heading)"

check_contains "$CLAUDE_CS" \
    "build-agent" \
    "Test 13a: Per-agent rubric table contains 'build-agent' row"

check_contains "$CLAUDE_CS" \
    "decide-agent" \
    "Test 13b: Per-agent rubric table contains 'decide-agent' row"

echo ""

# -------------------------------------------------------
# Tests 15-19: Content checks on 01-pipeline-orchestration.md
# -------------------------------------------------------
echo "--- 01-pipeline-orchestration.md insertions ---"

check_contains "$CLAUDE_PO" \
    "Score-check (inline, MANDATORY)" \
    "Test 15: Contains 'Score-check (inline, MANDATORY)' text (Insertion A)"

check_contains "$CLAUDE_PO" \
    "3a. READ CONFIDENCE SCORE" \
    "Test 16: Contains '3a. READ CONFIDENCE SCORE' text (Insertion B)"

check_contains "$CLAUDE_PO" \
    "CONFIDENCE SCORE ENFORCEMENT" \
    "Test 17: Contains 'CONFIDENCE SCORE ENFORCEMENT' text (Insertion C — rule 12)"

check_contains "$CLAUDE_PO" \
    "NEVER tell an agent to output a higher score" \
    "Test 18: Contains 'NEVER tell an agent to output a higher score' text"

check_contains "$CLAUDE_PO" \
    "**FAIL**" \
    "Test 19: Rule 01 workflow marks sub-90 / missing block as FAIL for rerun"

echo ""

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
echo "=========================================="
echo "Confidence Scoring Rules - Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    exit 1
fi
exit 0
