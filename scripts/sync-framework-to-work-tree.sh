#!/usr/bin/env bash
# Push multi-agent framework files from this repo into other projects under ~/WORK.
# Only touches: .claude/ .opencode/ .ai/README.md CLAUDE.md AGENTS.md
# Does NOT use rsync --delete (never removes extra files in targets).
# Does NOT touch application source trees.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
WORK_ROOT="${WORK_ROOT:-$HOME/WORK}"

if [[ ! -d "$WORK_ROOT" ]]; then
  echo "WORK_ROOT not found: $WORK_ROOT" >&2
  exit 1
fi

collect_targets() {
  local top
  # Every immediate child directory of WORK_ROOT
  for top in "$WORK_ROOT"/*/; do
    [[ -d "$top" ]] || continue
    printf '%s\n' "${top%/}"
  done
  # Nested git worktrees (e.g. Journal/App, Insight/lab) up to depth 4 under each top
  for top in "$WORK_ROOT"/*/; do
    [[ -d "$top" ]] || continue
    find "$top" -maxdepth 4 -type d -name .git 2>/dev/null | sed 's|/.git$||'
  done
}

echo "Source: $SRC"
REAL_SRC="$(cd "$SRC" && pwd -P)"
TARGETS_FILE="$(mktemp)"
collect_targets | sort -u >"$TARGETS_FILE"
COUNT="$(wc -l <"$TARGETS_FILE" | tr -d ' ')"
echo "Targets: $COUNT repo(s)/folder(s)"
echo "---"

while IFS= read -r DEST; do
  [[ -d "$DEST" ]] || continue
  if [[ "$(cd "$DEST" && pwd -P)" == "$REAL_SRC" ]]; then
    echo "→ $DEST (skip: canonical source repo)"
    continue
  fi

  echo "→ $DEST"
  mkdir -p "$DEST/.ai"
  rsync -a "$SRC/.claude/" "$DEST/.claude/"
  rsync -a "$SRC/.opencode/" "$DEST/.opencode/"
  rsync -a "$SRC/.ai/" "$DEST/.ai/"
  install -m 0644 "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"
  install -m 0644 "$SRC/AGENTS.md" "$DEST/AGENTS.md"
done <"$TARGETS_FILE"

rm -f "$TARGETS_FILE"

echo "---"
echo "Done. Framework paths only; no --delete; application code untouched."
