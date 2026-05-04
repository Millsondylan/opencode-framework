#!/usr/bin/env bash
# test_em_dash_block.sh
# Exercises .claude/hooks/pre_tool_use.py across its four policy layers:
# banned dashes, secrets, banned email libraries, and destructive shell.
#
# Payloads are constructed via python3 heredocs so this source file itself
# contains zero literal em, en, figure, or horizontal-bar glyphs, and no
# literal secret token prefixes.
#
# Run: bash .claude/hooks/tests/test_em_dash_block.sh

set -euo pipefail

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
NC=$'\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HOOK="$PROJECT_ROOT/.claude/hooks/pre_tool_use.py"

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

echo "=========================================="
echo "pre_tool_use.py Policy Tests"
echo "=========================================="
echo ""

if [[ ! -f "$HOOK" ]]; then
  fail "pre_tool_use.py not found at $HOOK"
  echo ""
  echo "Summary: $PASSED passed, $FAILED failed"
  exit $FAILED
fi

# run_hook <payload> : sets STDOUT and RC globals from the hook invocation.
# Uses a temp file to capture stdout while preserving the exit code.
run_hook() {
  local payload="$1"
  local tmp
  tmp="$(mktemp)"
  set +e
  printf '%s' "$payload" | python3 "$HOOK" >"$tmp" 2>/dev/null
  RC=$?
  set -e
  STDOUT="$(cat "$tmp")"
  rm -f "$tmp"
}

# --- Test 1: em-dash U+2014 blocked ---
PAYLOAD=$(python3 -c 'import json; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"/tmp/x.txt","content":"hello"+chr(0x2014)+"world"}}))')
run_hook "$PAYLOAD"
if [[ $RC -ne 0 ]] && echo "$STDOUT" | grep -q '"decision": *"block"' && echo "$STDOUT" | grep -iq 'dash'; then
  pass "T1: em-dash (U+2014) blocked"
else
  fail "T1: em-dash not blocked correctly (rc=$RC, stdout=$STDOUT)"
fi

# --- Test 2: en-dash U+2013 blocked ---
PAYLOAD=$(python3 -c 'import json; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"/tmp/x.txt","content":"a"+chr(0x2013)+"b"}}))')
run_hook "$PAYLOAD"
if [[ $RC -ne 0 ]] && echo "$STDOUT" | grep -q '"decision": *"block"' && echo "$STDOUT" | grep -iq 'dash'; then
  pass "T2: en-dash (U+2013) blocked"
else
  fail "T2: en-dash not blocked correctly (rc=$RC, stdout=$STDOUT)"
fi

# --- Test 3: clean ASCII content approved ---
PAYLOAD=$(python3 -c 'import json; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"/tmp/x.txt","content":"hello-world, this is fine."}}))')
run_hook "$PAYLOAD"
if [[ $RC -eq 0 ]] && echo "$STDOUT" | grep -q '"decision": *"approve"'; then
  pass "T3: clean ASCII content approved"
else
  fail "T3: clean content not approved (rc=$RC, stdout=$STDOUT)"
fi

# --- Test 4: secret pattern blocked ---
# Build the Anthropic-style key from fragments so this source contains no literal prefix.
PAYLOAD=$(python3 -c 'import json; prefix="sk"+"-"+"ant"+"-"; key=prefix+"abcdefghij1234567890"; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"/tmp/x.txt","content":"key="+key}}))')
run_hook "$PAYLOAD"
if [[ $RC -ne 0 ]] && echo "$STDOUT" | grep -q '"decision": *"block"' && echo "$STDOUT" | grep -iq 'secret'; then
  pass "T4: anthropic secret pattern blocked"
else
  fail "T4: secret not blocked correctly (rc=$RC, stdout=$STDOUT)"
fi

# --- Test 5: SMTP import blocked ---
PAYLOAD=$(python3 -c 'import json; print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"/tmp/x.py","content":"import smtplib\nclient=smtplib.SMTP()"}}))')
run_hook "$PAYLOAD"
if [[ $RC -ne 0 ]] && echo "$STDOUT" | grep -q '"decision": *"block"'; then
  pass "T5: SMTP import blocked"
else
  fail "T5: SMTP import not blocked (rc=$RC, stdout=$STDOUT)"
fi

# --- Test 6: destructive shell blocked without token ---
PAYLOAD=$(python3 -c 'import json; print(json.dumps({"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"}}))')
run_hook "$PAYLOAD"
if [[ $RC -ne 0 ]] && echo "$STDOUT" | grep -q '"decision": *"block"'; then
  pass "T6: destructive rm blocked without confirm token"
else
  fail "T6: destructive rm not blocked (rc=$RC, stdout=$STDOUT)"
fi

# --- Test 7: destructive shell approved with CONFIRM_DESTRUCTIVE token ---
PAYLOAD=$(python3 -c 'import json; print(json.dumps({"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo # CONFIRM_DESTRUCTIVE"}}))')
run_hook "$PAYLOAD"
if [[ $RC -eq 0 ]] && echo "$STDOUT" | grep -q '"decision": *"approve"'; then
  pass "T7: destructive rm approved with CONFIRM_DESTRUCTIVE"
else
  fail "T7: destructive rm with token not approved (rc=$RC, stdout=$STDOUT)"
fi

# --- Test 8: malformed stdin approved (fail-open) ---
run_hook "not json at all"
if [[ $RC -eq 0 ]] && echo "$STDOUT" | grep -q '"decision": *"approve"'; then
  pass "T8: malformed stdin fails open (approve)"
else
  fail "T8: malformed stdin not approved (rc=$RC, stdout=$STDOUT)"
fi

echo ""
echo "=========================================="
echo "Summary: $PASSED passed, $FAILED failed"
echo "=========================================="
exit $FAILED
