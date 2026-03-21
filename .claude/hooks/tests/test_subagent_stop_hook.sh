#!/usr/bin/env bash
# Smoke tests for subagent-stop-skill-reminder.py (SubagentStop hook command)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PY="$HOOKS_DIR/subagent-stop-skill-reminder.py"
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
fail=0

check_json() {
  local name="$1" json="$2"
  if echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('hookSpecificOutput',{}).get('hookEventName')=='SubagentStop'; assert 'additionalContext' in d.get('hookSpecificOutput',{})" 2>/dev/null; then
    echo -e "${GREEN}PASS${NC}: $name"
  else
    echo -e "${RED}FAIL${NC}: $name"
    echo "$json"
    fail=1
  fi
}

echo "=== SubagentStop hook (subagent-stop-skill-reminder.py) ==="

out=$(echo '{"agent_type":"build-agent-1","cwd":"/tmp"}' | python3 "$PY")
check_json "build-agent-1 sample" "$out"

out=$(echo '{"agent_type":"test-writer","cwd":"/tmp"}' | python3 "$PY")
check_json "test-writer sample" "$out"

out=$(echo '{"agent_type":"docs-researcher","cwd":"/tmp"}' | python3 "$PY")
check_json "docs-researcher sample" "$out"

out=$(echo 'not json' | python3 "$PY")
if [[ -z "${out// }" ]]; then
  echo -e "${GREEN}PASS${NC}: invalid stdin exits with no stdout (or empty)"
else
  # script prints JSON on success; on JSON error it exits 0 with no print - verify
  if echo "$out" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo -e "${RED}FAIL${NC}: invalid stdin should not emit valid hook JSON"
    fail=1
  else
    echo -e "${GREEN}PASS${NC}: invalid stdin does not emit valid JSON"
  fi
fi

exit "$fail"
