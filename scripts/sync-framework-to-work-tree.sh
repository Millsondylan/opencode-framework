#!/usr/bin/env bash
# Push multi-agent framework files from this repo into projects under ~/WORK (or WORK_ROOT).
#
# Copies only: .claude/ .opencode/ .ai/ CLAUDE.md AGENTS.md
# Never uses rsync --delete (extra files in targets are kept).
# Never touches application source outside those paths.
#
# Target discovery (union, de-duplicated):
#   1) Every immediate child directory of WORK_ROOT (e.g. ~/WORK/MyApp)
#   2) Every git repository root under WORK_ROOT (finds nested repos), with heavy dirs pruned
#
# Usage:
#   ./scripts/sync-framework-to-work-tree.sh           # sync
#   ./scripts/sync-framework-to-work-tree.sh --dry-run
#   ./scripts/sync-framework-to-work-tree.sh --list-only
#
# Env:
#   WORK_ROOT=/path          # default: $HOME/WORK
#   GIT_FIND_MAXDEPTH=n      # max depth under each top-level project for finding nested .git (default: 8)

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
WORK_ROOT="${WORK_ROOT:-$HOME/WORK}"

DRY_RUN=0
LIST_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --list-only) LIST_ONLY=1 ;;
    *)
      echo "Unknown option: $arg (use --dry-run or --list-only)" >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "$WORK_ROOT" ]]; then
  echo "WORK_ROOT not found: $WORK_ROOT" >&2
  exit 1
fi

# Git repo roots under each top-level WORK subtree (maxdepth avoids scanning huge dirs).
# Increase GIT_FIND_MAXDEPTH if you keep repos deeper than 6 levels under a project name.
GIT_FIND_MAXDEPTH="${GIT_FIND_MAXDEPTH:-8}"

collect_git_roots() {
  local top
  for top in "$WORK_ROOT"/*/; do
    [[ -d "$top" ]] || continue
    find "$top" -maxdepth "$GIT_FIND_MAXDEPTH" \
      \( -path '*/node_modules' -o -path '*/node_modules/*' \) -prune -o \
      \( -path '*/.dart_tool' -o -path '*/.dart_tool/*' \) -prune -o \
      \( -path '*/build' -o -path '*/build/*' \) -prune -o \
      \( -path '*/.git/*' \) -prune -o \
      \( -path '*/dist' -o -path '*/dist/*' \) -prune -o \
      \( -path '*/.next' -o -path '*/.next/*' \) -prune -o \
      \( -path '*/coverage' -o -path '*/coverage/*' \) -prune -o \
      \( -path '*/test-results' -o -path '*/test-results/*' \) -prune -o \
      \( -path '*/playwright-report' -o -path '*/playwright-report/*' \) -prune -o \
      \( -path '*/.pnpm-store' -o -path '*/.pnpm-store/*' \) -prune -o \
      \( -path '*/Pods' -o -path '*/Pods/*' \) -prune -o \
      \( -path '*/DerivedData' -o -path '*/DerivedData/*' \) -prune -o \
      \( -path '*/.venv' -o -path '*/.venv/*' \) -prune -o \
      \( -path '*/venv' -o -path '*/venv/*' \) -prune -o \
      \( -path '*/__pycache__' -o -path '*/__pycache__/*' \) -prune -o \
      \( -path '*/.gradle' -o -path '*/.gradle/*' \) -prune -o \
      \( -path '*/.idea' -o -path '*/.idea/*' \) -prune -o \
      -type d -name .git -print 2>/dev/null \
      | sed 's|/.git$||'
  done
}

collect_targets() {
  local top
  for top in "$WORK_ROOT"/*/; do
    [[ -d "$top" ]] || continue
    printf '%s\n' "${top%/}"
  done
  collect_git_roots
}

echo "Source: $SRC"
echo "WORK_ROOT: $WORK_ROOT"
REAL_SRC="$(cd "$SRC" && pwd -P)"
TARGETS_FILE="$(mktemp)"
collect_targets | sort -u >"$TARGETS_FILE"
COUNT="$(wc -l <"$TARGETS_FILE" | tr -d ' ')"
echo "Targets discovered: $COUNT"
echo "---"

if [[ "$LIST_ONLY" -eq 1 ]]; then
  cat "$TARGETS_FILE"
  rm -f "$TARGETS_FILE"
  exit 0
fi

while IFS= read -r DEST; do
  [[ -d "$DEST" ]] || continue
  if [[ "$(cd "$DEST" && pwd -P)" == "$REAL_SRC" ]]; then
    echo "→ $DEST (skip: canonical source repo)"
    continue
  fi

  echo "→ $DEST"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "   [dry-run] would: rsync .claude .opencode .ai + install CLAUDE.md AGENTS.md"
    continue
  fi

  mkdir -p "$DEST/.ai"
  rsync -a "$SRC/.claude/" "$DEST/.claude/"
  rsync -a "$SRC/.opencode/" "$DEST/.opencode/"
  rsync -a "$SRC/.ai/" "$DEST/.ai/"
  install -m 0644 "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"
  install -m 0644 "$SRC/AGENTS.md" "$DEST/AGENTS.md"
done <"$TARGETS_FILE"

rm -f "$TARGETS_FILE"

echo "---"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run only — no files were written."
else
  echo "Done. Framework paths only; no --delete; application code untouched."
fi
