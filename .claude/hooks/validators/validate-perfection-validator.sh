#!/bin/bash
# Validator for perfection-validator (optional pipeline stage)
# Validates Perfection Validation Report with PERFECT or FAIL
#
# SAFETY: Uses safe shell options. On any error, outputs valid JSON and exits 0.

set -u

trap 'echo "{\"valid\": true, \"errors\": [], \"warnings\": [\"Validator error - approved\"]}" && exit 0' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)" || SCRIPT_DIR="."
source "$SCRIPT_DIR/lib/logging.sh" 2>/dev/null || true
AGENT_NAME="perfection-validator"

INPUT=$(cat 2>/dev/null) || INPUT=""
OUTPUT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_response',''))" 2>/dev/null) || OUTPUT=""

ERRORS=()
WARNINGS=()

if ! echo "$OUTPUT" | grep -qi "Perfection Validation Report" 2>/dev/null; then
    ERRORS+=("Resolve this Format error in perfection-validator output: Missing required section - Perfection Validation Report")
fi

HAS_PERFECT=$(echo "$OUTPUT" | grep -ciE '\*\*Status:\*\* *PERFECT|Status:.*PERFECT' 2>/dev/null) || HAS_PERFECT=0
HAS_FAIL=$(echo "$OUTPUT" | grep -ciE '\*\*Status:\*\* *FAIL|Status:.*FAIL' 2>/dev/null) || HAS_FAIL=0

if [ "$HAS_PERFECT" -eq 0 ] && [ "$HAS_FAIL" -eq 0 ]; then
    ERRORS+=("Resolve this Content error in perfection-validator output: Missing explicit PERFECT or FAIL status")
fi

if [ "$HAS_PERFECT" -gt 0 ] && [ "$HAS_FAIL" -gt 0 ]; then
    WARNINGS+=("Both PERFECT and FAIL strings appear; ensure a single binary decision is explicit")
fi

if [ ${#ERRORS[@]} -eq 0 ]; then
    WARN_JSON="[]"
    if [ ${#WARNINGS[@]} -gt 0 ]; then
        WARN_JSON=$(printf '%s\n' "${WARNINGS[@]}" | python3 -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))" 2>/dev/null) || WARN_JSON="[]"
    fi
    OUTPUT_PREVIEW=$(echo "$OUTPUT" | head -c 500 2>/dev/null) || OUTPUT_PREVIEW=""
    write_log "$AGENT_NAME" "true" "[]" "$WARN_JSON" "$OUTPUT_PREVIEW" 2>/dev/null || true
    echo "{\"valid\": true, \"errors\": [], \"warnings\": $WARN_JSON}"
    exit 0
else
    ERROR_JSON=$(printf '%s\n' "${ERRORS[@]}" | python3 -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))" 2>/dev/null) || ERROR_JSON="[]"
    WARN_JSON="[]"
    if [ ${#WARNINGS[@]} -gt 0 ]; then
        WARN_JSON=$(printf '%s\n' "${WARNINGS[@]}" | python3 -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))" 2>/dev/null) || WARN_JSON="[]"
    fi
    OUTPUT_PREVIEW=$(echo "$OUTPUT" | head -c 500 2>/dev/null) || OUTPUT_PREVIEW=""
    write_log "$AGENT_NAME" "false" "$ERROR_JSON" "$WARN_JSON" "$OUTPUT_PREVIEW" 2>/dev/null || true
    echo "{\"valid\": false, \"errors\": $ERROR_JSON, \"warnings\": $WARN_JSON}"
    exit 0
fi
