#!/usr/bin/env python3
"""Bulk upgrade agents and skills with version, tier, critical frontmatter.

Adds the following fields to frontmatter blocks (between leading `---` markers):

Agents (.claude/agents/*.md):
  version: 1.0.0
  tier: critical   (when model is opus)    or  tier: standard   (when model is sonnet)
  critical: true   (when tier is critical) or  critical: false  (when tier is standard)

Skills (.claude/skills/*/SKILL.md):
  version: 1.0.0
  tier: standard

Idempotent: if a version field is already present, the file is skipped.
Uses only stdlib. No banned dash characters.
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

VERSION = "1.0.0"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split text into (frontmatter_body, rest). Returns (None, text) if no frontmatter."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def has_key(frontmatter: str, key: str) -> bool:
    pattern = re.compile(rf"^{re.escape(key)}\s*:", re.MULTILINE)
    return bool(pattern.search(frontmatter))


def detect_model(frontmatter: str) -> str | None:
    m = re.search(r"^model\s*:\s*([A-Za-z0-9_.-]+)", frontmatter, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip()


def append_fields(frontmatter: str, fields: list[tuple[str, str]]) -> str:
    body = frontmatter.rstrip("\n")
    additions = "\n".join(f"{k}: {v}" for k, v in fields)
    return body + "\n" + additions + "\n"


def rebuild(frontmatter: str, rest: str) -> str:
    if not frontmatter.endswith("\n"):
        frontmatter = frontmatter + "\n"
    return "---\n" + frontmatter + "---\n" + rest


def upgrade_agent(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    fm, rest = split_frontmatter(text)
    if fm is None:
        return "no-frontmatter"
    if has_key(fm, "version"):
        return "already-versioned"

    model = detect_model(fm)
    if model == "opus":
        tier = "critical"
        critical = "true"
    elif model == "sonnet":
        tier = "standard"
        critical = "false"
    else:
        # Default unknown models to standard, non-critical.
        tier = "standard"
        critical = "false"

    fields: list[tuple[str, str]] = [
        ("version", VERSION),
        ("tier", tier),
        ("critical", critical),
    ]
    new_fm = append_fields(fm, fields)
    path.write_text(rebuild(new_fm, rest), encoding="utf-8")
    return "upgraded"


def upgrade_skill(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    fm, rest = split_frontmatter(text)
    if fm is None:
        return "no-frontmatter"
    if has_key(fm, "version"):
        return "already-versioned"

    fields: list[tuple[str, str]] = [
        ("version", VERSION),
        ("tier", "standard"),
    ]
    new_fm = append_fields(fm, fields)
    path.write_text(rebuild(new_fm, rest), encoding="utf-8")
    return "upgraded"


def iter_agent_files() -> Iterable[pathlib.Path]:
    if not AGENTS_DIR.is_dir():
        return []
    return sorted(AGENTS_DIR.glob("*.md"))


def iter_skill_files() -> Iterable[pathlib.Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


def main(argv: list[str]) -> int:
    agents_upgraded = 0
    agents_skipped = 0
    agents_no_fm = 0

    for path in iter_agent_files():
        status = upgrade_agent(path)
        if status == "upgraded":
            agents_upgraded += 1
        elif status == "already-versioned":
            agents_skipped += 1
            print(f"skip (already versioned): {path.relative_to(REPO_ROOT)}")
        elif status == "no-frontmatter":
            agents_no_fm += 1
            print(f"skip (no frontmatter):    {path.relative_to(REPO_ROOT)}")

    skills_upgraded = 0
    skills_skipped = 0
    skills_no_fm = 0

    for path in iter_skill_files():
        status = upgrade_skill(path)
        if status == "upgraded":
            skills_upgraded += 1
        elif status == "already-versioned":
            skills_skipped += 1
            print(f"skip (already versioned): {path.relative_to(REPO_ROOT)}")
        elif status == "no-frontmatter":
            skills_no_fm += 1
            print(f"skip (no frontmatter):    {path.relative_to(REPO_ROOT)}")

    print()
    print("Summary")
    print(f"  agents upgraded:        {agents_upgraded}")
    print(f"  agents skipped (ver):   {agents_skipped}")
    print(f"  agents skipped (no fm): {agents_no_fm}")
    print(f"  skills upgraded:        {skills_upgraded}")
    print(f"  skills skipped (ver):   {skills_skipped}")
    print(f"  skills skipped (no fm): {skills_no_fm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
