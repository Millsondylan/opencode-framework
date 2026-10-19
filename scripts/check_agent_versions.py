#!/usr/bin/env python3
"""Validate versioning frontmatter on all agents and skills.

Checks:
  Agents (.claude/agents/*.md, skipping files without frontmatter):
    - version matches semver (^\\d+\\.\\d+\\.\\d+$)
    - tier in {critical, standard}
    - critical in {true, false}
    - tier/critical agreement: critical -> true, standard -> false

  Skills (.claude/skills/*/SKILL.md):
    - version matches semver
    - tier in {critical, standard}

Exit 0 when all valid, 1 when any violation found.
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
VALID_TIERS = {"critical", "standard"}
VALID_CRITICAL = {"true", "false"}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_frontmatter(text: str) -> str | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    return m.group(1)


def parse_scalar(frontmatter: str, key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}\s*:\s*(.+?)\s*$", re.MULTILINE)
    m = pattern.search(frontmatter)
    if not m:
        return None
    value = m.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return value


def iter_agent_files() -> Iterable[pathlib.Path]:
    if not AGENTS_DIR.is_dir():
        return []
    return sorted(AGENTS_DIR.glob("*.md"))


def iter_skill_files() -> Iterable[pathlib.Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


def check_agent(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    fm = extract_frontmatter(text)
    if fm is None:
        return []  # Files without frontmatter are out of scope.

    rel = str(path.relative_to(REPO_ROOT))
    violations: list[str] = []

    version = parse_scalar(fm, "version")
    if version is None:
        violations.append(f"{rel}: missing version")
    elif not SEMVER_RE.match(version):
        violations.append(f"{rel}: invalid semver: {version!r}")

    tier = parse_scalar(fm, "tier")
    if tier is None:
        violations.append(f"{rel}: missing tier")
    elif tier not in VALID_TIERS:
        violations.append(f"{rel}: invalid tier: {tier!r}")

    critical = parse_scalar(fm, "critical")
    if critical is None:
        violations.append(f"{rel}: missing critical")
    elif critical not in VALID_CRITICAL:
        violations.append(f"{rel}: invalid critical: {critical!r}")

    if tier == "critical" and critical == "false":
        violations.append(f"{rel}: tier=critical but critical=false")
    if tier == "standard" and critical == "true":
        violations.append(f"{rel}: tier=standard but critical=true")

    return violations


def check_skill(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    fm = extract_frontmatter(text)
    if fm is None:
        return []

    rel = str(path.relative_to(REPO_ROOT))
    violations: list[str] = []

    version = parse_scalar(fm, "version")
    if version is None:
        violations.append(f"{rel}: missing version")
    elif not SEMVER_RE.match(version):
        violations.append(f"{rel}: invalid semver: {version!r}")

    tier = parse_scalar(fm, "tier")
    if tier is None:
        violations.append(f"{rel}: missing tier")
    elif tier not in VALID_TIERS:
        violations.append(f"{rel}: invalid tier: {tier!r}")

    return violations


def main(argv: list[str]) -> int:
    all_violations: list[str] = []
    agents_checked = 0
    skills_checked = 0

    for path in iter_agent_files():
        agents_checked += 1
        all_violations.extend(check_agent(path))

    for path in iter_skill_files():
        skills_checked += 1
        all_violations.extend(check_skill(path))

    print(f"agents checked: {agents_checked}")
    print(f"skills checked: {skills_checked}")
    print(f"violations:     {len(all_violations)}")

    if all_violations:
        print()
        print("Violations:")
        for v in all_violations:
            print(f"  {v}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
