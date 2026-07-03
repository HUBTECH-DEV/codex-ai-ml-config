#!/usr/bin/env python3
"""Build a deterministic role index from the versioned Markdown library."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY = ROOT / ".promptsLibrary" / "role-prompts-ti-senior.md"
DEFAULT_OUTPUT = ROOT / ".promptsLibrary" / "role-index.json"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


def build_index(library: Path) -> dict[str, object]:
    lines = library.read_text(encoding="utf-8").splitlines()
    section = ""
    roles: list[dict[str, str]] = []

    for position, line in enumerate(lines):
        section_match = re.match(r"^# (?:\d+\.\s+)?(.+)$", line)
        if section_match:
            section = section_match.group(1).strip()
            continue

        role_match = re.match(r"^## (Principal .+)$", line)
        if not role_match:
            continue

        name = role_match.group(1).strip()
        area = ""
        for candidate in lines[position + 1 : position + 12]:
            area_match = re.match(r"^\*\*Área:\*\*\s*(.+?)\.?$", candidate)
            if area_match:
                area = area_match.group(1).strip()
                break

        roles.append(
            {
                "id": slugify(name),
                "name": name,
                "area": area,
                "section": section,
                "seniority": "principal",
            }
        )

    if not roles:
        raise ValueError("no Principal roles found")
    if len({role["id"] for role in roles}) != len(roles):
        raise ValueError("duplicate role ids found")

    return {
        "schemaVersion": "1.0",
        "libraryFile": ".promptsLibrary/role-prompts-ti-senior.md",
        "defaultBehavior": {
            "tone": "logical_analytical_direct",
            "decisionPolicy": "explicit_human_decision_when_required",
            "operatingMode": "discovery_first",
            "documentationTarget": "GitLab CE",
        },
        "roles": roles,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    content = json.dumps(
        build_index(args.library.resolve()),
        ensure_ascii=False,
        indent=2,
    ) + "\n"

    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != content:
            raise SystemExit("role index is missing or stale")
        print("role_index=valid")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(f"role_index={args.output} roles={len(json.loads(content)['roles'])}")


if __name__ == "__main__":
    main()

