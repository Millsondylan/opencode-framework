#!/usr/bin/env bash
# run-sync-all-targets.sh
# Sync OpenCode to all Run 2 targets. Invokes sync-opencode-run2.sh for each target.
# Run from repo root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_PATH="/Users/dyl/WORK"

TARGETS=(
  AIWebOptimizer
  Breathe
  EyeGuard
  Gymcicrle
  KIMI
  Mobile_agents
  MoneyWise
  Posturepilot
)

EXTRA_PATHS=(
  /Volumes/Code_system/work/JARVIS
)

EXCLUDE=(agents_web Claude-code-agents opencode-framework breathflow-privacy)

cd "$REPO_ROOT"

for target in "${TARGETS[@]}"; do
  skip=0
  for ex in "${EXCLUDE[@]}"; do
    [[ "$target" == "$ex" ]] && { skip=1; break; }
  done
  [[ $skip -eq 1 ]] && { echo "Skipping $target (excluded)"; continue; }
  target_path="$BASE_PATH/$target"
  echo "=== Syncing $target ==="
  "$SCRIPT_DIR/sync-opencode-run2.sh" "$target_path"
  echo ""
done

for target_path in "${EXTRA_PATHS[@]}"; do
  [[ ! -d "$target_path" ]] && { echo "Skipping $target_path (not a directory)"; continue; }
  echo "=== Syncing $target_path ==="
  "$SCRIPT_DIR/sync-opencode-run2.sh" "$target_path"
  echo ""
done

echo "All targets synced."
