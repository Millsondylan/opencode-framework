#!/usr/bin/env bash
# Minimal verification script for build-agent skill activation.
# Validates setup and prints instructions. Actual dispatch requires orchestrator/task tool.

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILL_PATH="$REPO_ROOT/.opencode/skills/auth-schema/SKILL.md"
VERIFY_PROMPT="$REPO_ROOT/.opencode/prompts/verify-build-agent-skill.md"

echo "=== Build-Agent Skill Activation Verification ==="
echo ""

# Pre-flight checks
if [[ ! -f "$SKILL_PATH" ]]; then
  echo "FAIL: Skill file not found: $SKILL_PATH"
  exit 1
fi
echo "OK: Skill file exists: $SKILL_PATH"

if [[ ! -f "$VERIFY_PROMPT" ]]; then
  echo "FAIL: Verification prompt not found: $VERIFY_PROMPT"
  exit 1
fi
echo "OK: Verification prompt exists: $VERIFY_PROMPT"
echo ""

echo "=== Verification Instructions ==="
echo "1. Use the orchestrator to dispatch build-agent-1 with the prompt from:"
echo "   $VERIFY_PROMPT"
echo ""
echo "2. Ensure the prompt includes: skill: auth-schema"
echo ""
echo "3. After build-agent-1 completes, verify the checklist in the same file."
echo ""
echo "4. Full procedure: .opencode/prompts/VERIFICATION-PROCEDURE.md"
echo ""
echo "Pre-flight checks passed. Ready for verification."
