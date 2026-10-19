#!/usr/bin/env bash
# test_anti_orchestration_fix.sh
# Verifies the build-agent anti-orchestration fix (Run 1 + Run 2).
# Maps to: no "Nested Sub-Pipeline" in build-agents; "CRITICAL: You Are NOT the Orchestrator"
# in build-agent-1..55; SCOPE in 01-pipeline-orchestration; ORCHESTRATOR-ONLY in 03-agent-dispatch;
# EXCLUDE array in run-sync-all-targets.sh.
# NO mocks, NO placeholders. Real grep/file checks.
#
# Run: bash scripts/tests/test_anti_orchestration_fix.sh
# Or:  bash .claude/hooks/tests/run_all_tests.sh (includes this script)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/.opencode/agents"
RULES_DIR="$PROJECT_ROOT/.opencode/rules"
RUN_SYNC="$PROJECT_ROOT/scripts/run-sync-all-targets.sh"
FAILED=0

fail() {
  echo -e "${RED}FAIL${NC}: $1"
  FAILED=$((FAILED + 1))
}

pass() {
  echo -e "${GREEN}PASS${NC}: $1"
}

echo "=========================================="
echo "Build-Agent Anti-Orchestration Fix Verification"
echo "=========================================="
echo ""

# --- 1: No "Nested Sub-Pipeline" in build-agent files (grep count = 0) ---
NESTED_COUNT=$(grep -r "Nested Sub-Pipeline" "$AGENTS_DIR" 2>/dev/null || true | wc -l | tr -d ' ')
if [[ "$NESTED_COUNT" != "0" ]]; then
  fail "1: 'Nested Sub-Pipeline' found in build-agent files (count=$NESTED_COUNT, expected 0)"
else
  pass "1: No 'Nested Sub-Pipeline' in build-agent files (grep count=0)"
fi

# --- 2: "CRITICAL: You Are NOT the Orchestrator" in build-agent-1 through build-agent-55 ---
CRITICAL_PHRASE="CRITICAL: You Are NOT the Orchestrator"
MISSING_AGENTS=()
for i in $(seq 1 55); do
  f="$AGENTS_DIR/build-agent-$i.md"
  if [[ ! -f "$f" ]]; then
    MISSING_AGENTS+=("build-agent-$i.md (missing)")
  elif ! grep -q "$CRITICAL_PHRASE" "$f"; then
    MISSING_AGENTS+=("build-agent-$i.md (no CRITICAL phrase)")
  fi
done
if [[ ${#MISSING_AGENTS[@]} -gt 0 ]]; then
  fail "2: Missing CRITICAL phrase in: ${MISSING_AGENTS[*]}"
else
  pass "2: 'CRITICAL: You Are NOT the Orchestrator' in build-agent-1 through build-agent-55"
fi

# --- 3: SCOPE note in 01-pipeline-orchestration.md ---
PIPELINE_RULES="$RULES_DIR/01-pipeline-orchestration.md"
if [[ ! -f "$PIPELINE_RULES" ]]; then
  fail "3: 01-pipeline-orchestration.md does not exist"
elif ! grep -q "SCOPE" "$PIPELINE_RULES"; then
  fail "3: SCOPE note not found in 01-pipeline-orchestration.md"
else
  pass "3: SCOPE note present in 01-pipeline-orchestration.md"
fi

# --- 4: ORCHESTRATOR-ONLY note in 03-agent-dispatch.md ---
DISPATCH_RULES="$RULES_DIR/03-agent-dispatch.md"
if [[ ! -f "$DISPATCH_RULES" ]]; then
  fail "4: 03-agent-dispatch.md does not exist"
elif ! grep -q "ORCHESTRATOR-ONLY" "$DISPATCH_RULES"; then
  fail "4: ORCHESTRATOR-ONLY note not found in 03-agent-dispatch.md"
else
  pass "4: ORCHESTRATOR-ONLY note present in 03-agent-dispatch.md"
fi

# --- 5: EXCLUDE array in run-sync-all-targets.sh ---
if [[ ! -f "$RUN_SYNC" ]]; then
  fail "5: run-sync-all-targets.sh does not exist"
elif ! grep -qE '^EXCLUDE=\(' "$RUN_SYNC"; then
  fail "5: EXCLUDE array not found in run-sync-all-targets.sh"
elif ! grep -qE 'EXCLUDE\[@\]' "$RUN_SYNC" && ! grep -qE '\$\{EXCLUDE\[@\]\}' "$RUN_SYNC"; then
  fail "5: EXCLUDE array not used in exclusion logic"
else
  pass "5: EXCLUDE array present and used in run-sync-all-targets.sh"
fi

echo ""
echo "=========================================="
if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}All anti-orchestration fix verification tests passed.${NC}"
  exit 0
else
  echo -e "${RED}$FAILED test(s) failed.${NC}"
  exit 1
fi
