#!/usr/bin/env bash
# test_alibaba_fix.sh
# Verifies the Alibaba model fix implementation (Run 1 + Run 2).
# Maps to TaskSpec F1-F8. NO mocks, NO placeholders. Real grep/bash assertions.
#
# Run: bash scripts/tests/test_alibaba_fix.sh
# Or:  bash .claude/hooks/tests/run_all_tests.sh (includes this script)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FAILED=0

fail() {
  echo -e "${RED}FAIL${NC}: $1"
  FAILED=$((FAILED + 1))
}

pass() {
  echo -e "${GREEN}PASS${NC}: $1"
}

echo "=========================================="
echo "Alibaba Model Fix Verification (F1-F8)"
echo "=========================================="
echo ""

# --- F1: No alibaba-coding-plan in .opencode/ ---
ALIBA_OPENCODE=$(grep -r "alibaba-coding-plan" "$PROJECT_ROOT/.opencode" 2>/dev/null || true)
if [[ -n "$ALIBA_OPENCODE" ]]; then
  fail "F1: alibaba-coding-plan found in .opencode/: $ALIBA_OPENCODE"
else
  pass "F1: No alibaba-coding-plan in .opencode/"
fi

# --- F2: No alibaba-coding-plan in .ai/ ---
ALIBA_AI=$(grep -r "alibaba-coding-plan" "$PROJECT_ROOT/.ai" 2>/dev/null || true)
if [[ -n "$ALIBA_AI" ]]; then
  fail "F2: alibaba-coding-plan found in .ai/: $ALIBA_AI"
else
  pass "F2: No alibaba-coding-plan in .ai/"
fi

# --- F3: run-sync-all-targets.sh exists ---
RUN_SYNC="$PROJECT_ROOT/scripts/run-sync-all-targets.sh"
if [[ ! -f "$RUN_SYNC" ]]; then
  fail "F3: run-sync-all-targets.sh does not exist"
else
  pass "F3: run-sync-all-targets.sh exists"
fi

# --- F4: run-sync-all-targets.sh is executable ---
if [[ -f "$RUN_SYNC" ]] && [[ ! -x "$RUN_SYNC" ]]; then
  fail "F4: run-sync-all-targets.sh is not executable"
elif [[ -f "$RUN_SYNC" ]]; then
  pass "F4: run-sync-all-targets.sh is executable"
fi

# --- F5: run-sync-all-targets.sh has valid bash syntax ---
if [[ -f "$RUN_SYNC" ]]; then
  if ! bash -n "$RUN_SYNC" 2>/dev/null; then
    fail "F5: run-sync-all-targets.sh has invalid bash syntax"
  else
    pass "F5: run-sync-all-targets.sh has valid bash syntax"
  fi
fi

# --- F6: sync-opencode-run2.sh is invoked correctly by run-sync-all-targets.sh ---
if [[ -f "$RUN_SYNC" ]]; then
  if ! grep -q 'sync-opencode-run2\.sh' "$RUN_SYNC"; then
    fail "F6: run-sync-all-targets.sh does not invoke sync-opencode-run2.sh"
  elif ! grep -q '\$target_path' "$RUN_SYNC"; then
    fail "F6: sync-opencode-run2.sh must receive target_path as argument"
  else
    pass "F6: sync-opencode-run2.sh invoked correctly with target path"
  fi
fi

# --- F7: sync-opencode-run2.sh exists and has valid bash syntax ---
SYNC_RUN2="$PROJECT_ROOT/scripts/sync-opencode-run2.sh"
if [[ ! -f "$SYNC_RUN2" ]]; then
  fail "F7: sync-opencode-run2.sh does not exist"
else
  pass "F7: sync-opencode-run2.sh exists"
  if ! bash -n "$SYNC_RUN2" 2>/dev/null; then
    fail "F7b: sync-opencode-run2.sh has invalid bash syntax"
  else
    pass "F7b: sync-opencode-run2.sh has valid bash syntax"
  fi
fi

# --- F8: 8 targets configured in run-sync-all-targets.sh ---
if [[ -f "$RUN_SYNC" ]]; then
  REQUIRED_TARGETS=(AIWebOptimizer Breathe EyeGuard Gymcicrle KIMI Mobile_agents MoneyWise Posturepilot)
  MISSING=0
  for t in "${REQUIRED_TARGETS[@]}"; do
    if ! grep -q "$t" "$RUN_SYNC"; then
      fail "F8: Target $t not in run-sync-all-targets.sh"
      MISSING=$((MISSING + 1))
    fi
  done
  if [[ $MISSING -eq 0 ]]; then
    pass "F8: 8 targets configured in run-sync-all-targets.sh"
  fi
fi

echo ""
echo "=========================================="
if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}All Alibaba fix verification tests passed.${NC}"
  exit 0
else
  echo -e "${RED}$FAILED test(s) failed.${NC}"
  exit 1
fi
