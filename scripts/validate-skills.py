#!/usr/bin/env python3
"""Validate local Agent Skills and Markdown links without third-party packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
README_INSTALL = re.compile(r"--skill\s+([a-z0-9-]+)")


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}

    end = text.find("\n---\n", 4)
    if end < 0:
        return {}

    result: dict[str, str] = {}
    active_key: str | None = None
    for line in text[4:end].splitlines():
        match = re.match(r"^([a-zA-Z][\w-]*):\s*(.*)$", line)
        if match:
            active_key = match.group(1)
            value = match.group(2).strip()
            result[active_key] = "" if value in {">", "|"} else value
        elif active_key and line.startswith("  "):
            result[active_key] = f"{result[active_key]} {line.strip()}".strip()
    return result


def validate_skill(skill_file: Path) -> list[str]:
    errors: list[str] = []
    metadata = read_frontmatter(skill_file)
    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if not name:
        errors.append(f"{skill_file}: missing frontmatter name")
    elif not SKILL_NAME.fullmatch(name):
        errors.append(f"{skill_file}: invalid skill name {name!r}")
    elif name != skill_file.parent.name:
        errors.append(
            f"{skill_file}: name {name!r} does not match directory {skill_file.parent.name!r}"
        )

    if not description:
        errors.append(f"{skill_file}: missing frontmatter description")
    elif "<" in description or ">" in description:
        errors.append(f"{skill_file}: description cannot contain angle brackets")
    return errors


def validate_links(markdown_file: Path) -> list[str]:
    errors: list[str] = []
    text = markdown_file.read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(text):
        target = target.strip().split("#", 1)[0]
        if not target:
            continue
        if target.startswith("file://"):
            errors.append(f"{markdown_file}: local file URI is not portable: {target}")
            continue
        if re.match(r"^[a-z][a-z0-9+.-]*://", target, re.IGNORECASE):
            continue
        if not (markdown_file.parent / target).resolve().exists():
            errors.append(f"{markdown_file}: broken relative link: {target}")
    return errors


def main() -> int:
    skill_files = sorted(ROOT.glob("*/SKILL.md"))
    errors: list[str] = []
    if not skill_files:
        errors.append("No top-level skills found")

    for skill_file in skill_files:
        errors.extend(validate_skill(skill_file))

    actual_names = {read_frontmatter(path).get("name", "") for path in skill_files}
    readme = ROOT / "README.md"
    documented_names = set(README_INSTALL.findall(readme.read_text(encoding="utf-8")))
    if documented_names != actual_names:
        missing = sorted(actual_names - documented_names)
        stale = sorted(documented_names - actual_names)
        if missing:
            errors.append(f"README.md: missing install commands for {', '.join(missing)}")
        if stale:
            errors.append(f"README.md: stale install commands for {', '.join(stale)}")

    for markdown_file in sorted(ROOT.rglob("*.md")):
        if ".git" not in markdown_file.parts and ".codegraph" not in markdown_file.parts:
            errors.extend(validate_links(markdown_file))

    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error.replace(f'{ROOT}/', '')}")
        return 1

    print(f"Validated {len(skill_files)} skills and all local Markdown links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
