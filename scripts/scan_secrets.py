#!/usr/bin/env python3
"""Run a small dependency-free secret scan over the HubICG worktree."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}
PATTERNS = {
    "private-key": re.compile("-" * 5 + r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    "github-token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}


def candidate_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in SKIP_PARTS for part in path.parts)
        and path.stat().st_size <= 2_000_000
    )


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in candidate_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "secret-scan: allow" in line:
                continue
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    relative = path.relative_to(root).as_posix()
                    findings.append(f"{relative}:{line_number}:{label}")
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    findings = scan(root)
    if findings:
        for finding in findings:
            print(f"secret_scan=finding location={finding}")
        raise SystemExit(1)
    print("secret_scan=clean")


if __name__ == "__main__":
    main()
