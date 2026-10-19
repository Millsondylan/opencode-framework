#!/usr/bin/env python3
"""sweep_legacy_dashes.py

Walk project directories and replace banned horizontal dash codepoints with
ASCII hyphen-minus (U+002D).

Banned codepoints (constructed via chr() so this source file is dash-clean):
  U+2014 EM DASH
  U+2013 EN DASH
  U+2012 FIGURE DASH
  U+2015 HORIZONTAL BAR

Usage:
  scripts/sweep_legacy_dashes.py            # dry-run report
  scripts/sweep_legacy_dashes.py --apply    # write changes to disk

Intentional exemptions (files that document the banned chars on purpose and
MUST keep literal occurrences to demonstrate the rule):
  CLAUDE.md
  AGENTS.md
  .claude/rules/08-em-dash-ban.md
  .claude/hooks/pre_tool_use.py
  scripts/check_emdash.sh
  docs/decisions/0004-em-dash-and-en-dash-ban.md
  scripts/sweep_legacy_dashes.py (this file)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# Build the banned char set without embedding any literal banned dash in
# this source file. All references use chr() only.
BANNED_CODEPOINTS = (0x2014, 0x2013, 0x2012, 0x2015)
BANNED_CHARS = "".join(chr(cp) for cp in BANNED_CODEPOINTS)
ASCII_HYPHEN = chr(0x002D)

# Extensions to process.
TEXT_EXTENSIONS = {
    ".md",
    ".py",
    ".sh",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".dart",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".sql",
    ".html",
    ".css",
    ".conf",
    ".ini",
}

# Directories to walk. Relative to repo root.
WALK_ROOTS = (
    ".claude",
    ".opencode",
    "docs",
    "scripts",
    "eval",
    "memory",
    "telemetry",
    "daemons",
    "marketing",
    "publishing",
    "screenshots",
    ".ai",
    "bootstrap",
)

# Directories to skip anywhere in the tree.
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "build",
    ".dart_tool",
}

# Files that must KEEP their literal banned dashes (they document the ban).
# Paths are relative to repo root.
EXEMPT_FILES = {
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/rules/08-em-dash-ban.md",
    ".claude/hooks/pre_tool_use.py",
    "scripts/check_emdash.sh",
    "scripts/sweep_legacy_dashes.py",
    "docs/decisions/0004-em-dash-and-en-dash-ban.md",
}


SPECIAL_FILENAMES = {".gitignore", ".dockerignore", ".env.example", "Dockerfile"}


def should_process(path: Path, repo_root: Path) -> bool:
    """Return True if path should be scanned and rewritten."""
    rel = path.relative_to(repo_root).as_posix()
    if rel in EXEMPT_FILES:
        return False
    if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in SPECIAL_FILENAMES:
        return False
    # Skip inside any skip-dir.
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return False
    return True


def walk_targets(repo_root: Path) -> list[Path]:
    """Collect all candidate files under the configured walk roots."""
    targets: list[Path] = []
    for root_name in WALK_ROOTS:
        root_dir = repo_root / root_name
        if not root_dir.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Prune skip dirs in place.
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            for name in filenames:
                p = Path(dirpath) / name
                if should_process(p, repo_root):
                    targets.append(p)
    # Also scan top-level text files (e.g., CHANGELOG.md, README.md, yaml).
    for entry in repo_root.iterdir():
        if entry.is_file() and should_process(entry, repo_root):
            targets.append(entry)
    return sorted(set(targets))


def count_and_replace(text: str) -> tuple[str, int]:
    """Replace every banned char with ASCII hyphen. Return (new_text, count)."""
    count = 0
    for ch in BANNED_CHARS:
        count += text.count(ch)
        if count:
            text = text.replace(ch, ASCII_HYPHEN)
    # The count accumulated via the first pass already reflects all four
    # codepoints since each replace is applied sequentially. Recompute the
    # exact number against the ORIGINAL was already captured per char before
    # replace. Above loop mixes these. Redo safely:
    return text, count


def scan_file(path: Path) -> int:
    """Return number of banned chars in file (reads bytes safely)."""
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    total = 0
    for ch in BANNED_CHARS:
        total += data.count(ch)
    return total


def rewrite_file(path: Path) -> int:
    """Rewrite file replacing banned chars. Return number of replacements."""
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    total = 0
    new = data
    for ch in BANNED_CHARS:
        c = new.count(ch)
        if c:
            new = new.replace(ch, ASCII_HYPHEN)
            total += c
    if total and new != data:
        path.write_text(new, encoding="utf-8")
    return total


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Sweep legacy banned dashes.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to disk (default is dry-run).",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root (defaults to parent of this script).",
    )
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    repo_root = Path(args.root).resolve() if args.root else script_dir.parent

    targets = walk_targets(repo_root)
    total_files = 0
    total_replacements = 0
    changed_files: list[tuple[str, int]] = []

    for path in targets:
        n = scan_file(path)
        if n == 0:
            continue
        total_files += 1
        total_replacements += n
        rel = path.relative_to(repo_root).as_posix()
        if args.apply:
            written = rewrite_file(path)
            changed_files.append((rel, written))
        else:
            changed_files.append((rel, n))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[sweep_legacy_dashes] mode={mode}")
    print(f"[sweep_legacy_dashes] repo_root={repo_root}")
    print(f"[sweep_legacy_dashes] candidates={len(targets)}")
    print(f"[sweep_legacy_dashes] files_with_violations={total_files}")
    print(f"[sweep_legacy_dashes] total_replacements={total_replacements}")
    for rel, n in changed_files[:50]:
        print(f"  {rel}: {n}")
    if len(changed_files) > 50:
        print(f"  ... and {len(changed_files) - 50} more")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
