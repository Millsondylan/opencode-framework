#!/bin/bash
# Verification tests for confidence scoring rule files
#
# Verifies both 09-confidence-scoring.md copies and the edits to
# 01-pipeline-orchestration.md in both .opencode/rules/ and .claude/rules/.
#
# Run: bash .claude/hooks/tests/test_confidence_scoring_rules.sh
# Or via: bash .claude/hooks/tests/run_all_tests.sh

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

OPENCODE_CS="$PROJECT_ROOT/.opencode/rules/09-confidence-scoring.md"
CLAUDE_CS="$PROJECT_ROOT/.claude/rules/09-confidence-scoring.md"
OPENCODE_PO="$PROJECT_ROOT/.opencode/rules/01-pipeline-orchestration.md"
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

if [ -f "$OPENCODE_CS" ]; then
    pass "Test 1: .opencode/rules/09-confidence-scoring.md exists"
else
    fail "Test 1: .opencode/rules/09-confidence-scoring.md exists"
fi

if [ -f "$CLAUDE_CS" ]; then
    pass "Test 2: .claude/rules/09-confidence-scoring.md exists"
else
    fail "Test 2: .claude/rules/09-confidence-scoring.md exists"
fi

echo ""

# -------------------------------------------------------
# Test 3: Both copies are byte-for-byte identical
# -------------------------------------------------------
echo "--- 09-confidence-scoring.md parity ---"

if [ -f "$OPENCODE_CS" ] && [ -f "$CLAUDE_CS" ]; then
    if diff -q "$OPENCODE_CS" "$CLAUDE_CS" > /dev/null 2>&1; then
        pass "Test 3: Both 09-confidence-scoring.md copies are byte-for-byte identical"
    else
        fail "Test 3: Both 09-confidence-scoring.md copies are byte-for-byte identical (files differ)"
    fi
else
    fail "Test 3: Cannot compare — one or both 09-confidence-scoring.md files missing"
fi

echo ""

# -------------------------------------------------------
# Tests 4-12: Content checks on 09-confidence-scoring.md
# (Use the .opencode copy as canonical; both are identical per Test 3)
# -------------------------------------------------------
echo "--- 09-confidence-scoring.md content ---"

check_contains "$OPENCODE_CS" \
    "# Confidence Scoring System" \
    "Test 4: Contains '# Confidence Scoring System' heading"

check_contains "$OPENCODE_CS" \
    "0–59" \
    "Test 5a: Scoring table band 0-59 present"

check_contains "$OPENCODE_CS" \
    "60–84" \
    "Test 5b: Scoring table band 60-84 present"

check_contains "$OPENCODE_CS" \
    "85–94" \
    "Test 5c: Scoring table band 85-94 present"

check_contains "$OPENCODE_CS" \
    "95–100" \
    "Test 5d: Scoring table band 95-100 present"

check_contains "$OPENCODE_CS" \
    "Universal Rubric Template" \
    "Test 6: Contains 'Universal Rubric Template' section"

check_contains "$OPENCODE_CS" \
    "{score}" \
    "Test 7: Contains '{score}' placeholder token in CONFIDENCE block template"

check_contains "$OPENCODE_CS" \
    "{completeness}" \
    "Test 8: Contains '{completeness}' placeholder token"

check_contains "$OPENCODE_CS" \
    "Anti-Cheating" \
    "Test 9: Contains 'Anti-Cheating' section"

check_contains "$OPENCODE_CS" \
    "score < 85" \
    "Test 10: Contains '85' rerun threshold"

check_contains "$OPENCODE_CS" \
    "below 95" \
    "Test 11: Contains '95' pipeline flag threshold"

check_contains "$OPENCODE_CS" \
    "### CONFIDENCE" \
    "Test 12: Contains '### CONFIDENCE' heading (required output block heading)"

# Per-agent rubric table: check for build-agent and decide-agent rows
check_contains "$OPENCODE_CS" \
    "build-agent" \
    "Test 13a: Per-agent rubric table contains 'build-agent' row"

check_contains "$OPENCODE_CS" \
    "decide-agent" \
    "Test 13b: Per-agent rubric table contains 'decide-agent' row"

echo ""

# -------------------------------------------------------
# Test 14: Both 01-pipeline-orchestration.md copies are identical
# -------------------------------------------------------
echo "--- 01-pipeline-orchestration.md parity ---"

if [ -f "$OPENCODE_PO" ] && [ -f "$CLAUDE_PO" ]; then
    if diff -q "$OPENCODE_PO" "$CLAUDE_PO" > /dev/null 2>&1; then
        pass "Test 14: Both 01-pipeline-orchestration.md copies are byte-for-byte identical"
    else
        fail "Test 14: Both 01-pipeline-orchestration.md copies are byte-for-byte identical (files differ)"
    fi
else
    fail "Test 14: Cannot compare — one or both 01-pipeline-orchestration.md files missing"
fi

echo ""

# -------------------------------------------------------
# Tests 15-19: Content checks on 01-pipeline-orchestration.md insertions
# (Use .opencode copy as canonical)
# -------------------------------------------------------
echo "--- 01-pipeline-orchestration.md insertions ---"

check_contains "$OPENCODE_PO" \
    "Score-check (inline, MANDATORY)" \
    "Test 15: Contains 'Score-check (inline, MANDATORY)' text (Insertion A)"

check_contains "$OPENCODE_PO" \
    "3a. READ CONFIDENCE SCORE" \
    "Test 16: Contains '3a. READ CONFIDENCE SCORE' text (Insertion B)"

check_contains "$OPENCODE_PO" \
    "CONFIDENCE SCORE ENFORCEMENT" \
    "Test 17: Contains 'CONFIDENCE SCORE ENFORCEMENT' text (Insertion C — rule 12)"

check_contains "$OPENCODE_PO" \
    "NEVER tell an agent to output a higher score" \
    "Test 18: Contains 'NEVER tell an agent to output a higher score' text"

check_contains "$OPENCODE_PO" \
    "score = 0, mandatory rerun" \
    "Test 19: Contains 'score = 0, mandatory rerun' text"

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
