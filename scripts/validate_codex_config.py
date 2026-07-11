#!/usr/bin/env python3
"""Validate the consolidated Codex configuration and its audit chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_FIELDS = (
    "agentConfigurationPrompt",
    "agentProfile",
    "projectRules",
    "communicationRules",
    "technicalRules",
    "customInstructions",
    "metadata",
)


class ValidationError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid JSON {path}: {error}") from error


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    require(match is not None, f"missing frontmatter: {path}")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        require(bool(separator), f"invalid frontmatter line: {line}")
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, text


def validate_snapshot_chain(root: Path) -> int:
    active = read_json(root / ".promptsConfig" / "agentconfig.json")
    history = read_json(root / ".promptsConfig" / "agentconfig-history.json")

    require(active.get("schemaVersion") == "1.0", "unsupported agent config schema")
    current = active.get("currentVersion")
    require(isinstance(current, int) and current > 0, "invalid currentVersion")
    require(history.get("currentVersion") == current, "active/history version mismatch")

    versions = history.get("versions")
    require(isinstance(versions, list) and versions, "empty version history")
    numbers = [entry.get("version") for entry in versions]
    require(numbers == list(range(1, current + 1)), "version history is not contiguous")

    for entry in versions:
        snapshot_rel = entry.get("snapshotFile")
        require(isinstance(snapshot_rel, str), "snapshotFile is missing")
        snapshot = read_json(root / ".promptsConfig" / snapshot_rel)
        require(snapshot.get("version") == entry.get("version"), "snapshot version mismatch")

    latest = read_json(root / ".promptsConfig" / versions[-1]["snapshotFile"])
    expected = {
        "version": current,
        "createdAt": active.get("lastUpdated"),
        **{field: active.get(field) for field in SNAPSHOT_FIELDS},
    }
    require(latest == expected, "active configuration differs from latest snapshot")
    return current


def validate_context(root: Path) -> int:
    context = root / ".promptsConfig" / "codex-primary-context.md"
    metadata, text = parse_frontmatter(context)
    require(metadata.get("schemaVersion") == "1.0", "unsupported context schema")
    require(metadata.get("configId") == "codex-primary-context", "invalid configId")
    try:
        version = int(metadata["configVersion"])
    except (KeyError, ValueError) as error:
        raise ValidationError("invalid context configVersion") from error
    require(version > 0, "context version must be positive")
    require(bool(metadata.get("lastUpdated")), "context lastUpdated is missing")

    required_phrases = (
        "Já existe um repositório correspondente no GitHub/HUBTECH-DEV",
        "Autoriza iniciar a migração da documentação",
        "pull apenas fast-forward",
        "Principal AI/ML Engineer",
        "Principal DevOps Engineer",
    )
    for phrase in required_phrases:
        require(phrase in text, f"context rule missing: {phrase}")
    return version


def validate_role_library(root: Path) -> int:
    library = root / ".promptsLibrary" / "role-prompts-ti-senior.md"
    manifest = root / ".promptsLibrary" / "MANIFEST.sha256"
    index = read_json(root / ".promptsLibrary" / "role-index.json")

    require(library.is_file(), "role library is missing")
    require(manifest.is_file(), "role library manifest is missing")
    expected_hash = manifest.read_text(encoding="utf-8").split()[0]
    actual_hash = hashlib.sha256(library.read_bytes()).hexdigest()
    require(actual_hash == expected_hash, "role library checksum mismatch")

    roles = index.get("roles")
    require(isinstance(roles, list) and len(roles) >= 50, "role index is incomplete")
    require(
        index.get("libraryFile") == ".promptsLibrary/role-prompts-ti-senior.md",
        "role index points to a different library",
    )
    return len(roles)


def validate_prompt_histories(root: Path) -> int:
    files = sorted((root / ".promptsHistory").glob("*.json"))
    require(bool(files), "prompt history is empty")
    for path in files:
        data = read_json(path)
        require(bool(data.get("chatName")), f"chatName missing: {path}")
        require(isinstance(data.get("messages"), list), f"messages missing: {path}")
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__import__("os").environ.get("CODEX_CONFIG_REPO", DEFAULT_ROOT)),
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()

    try:
        agent_version = validate_snapshot_chain(root)
        context_version = validate_context(root)
        role_count = validate_role_library(root)
        history_count = validate_prompt_histories(root)
        require((root / "AGENTS.md").is_file(), "project AGENTS.md is missing")
        require(
            (root / "scripts" / "sync_codex_config.py").is_file(),
            "sync script is missing",
        )
    except (OSError, ValidationError) as error:
        print(f"codex_config=invalid error={error}", file=sys.stderr)
        raise SystemExit(1)

    if not args.quiet:
        print(
            "codex_config=valid "
            f"agent_version={agent_version} "
            f"context_version={context_version} "
            f"roles={role_count} "
            f"prompt_histories={history_count}"
        )


if __name__ == "__main__":
    main()
