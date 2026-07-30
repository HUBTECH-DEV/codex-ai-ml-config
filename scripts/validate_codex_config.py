#!/usr/bin/env python3
"""Validate HubICG configuration, schemas, roles and append-only audit records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from build_role_index import build_index
from validate_schemas import SchemaValidationError, validate_all


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
MESSAGE_ROLES = {"system", "developer", "user", "assistant", "tool"}
RFC3339_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:\d{2})$"
)


class ValidationError(RuntimeError):
    """Raised when the versioned framework is internally inconsistent."""


def read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid JSON {path}: {error}") from error
    require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_timestamp(value: object, field: str) -> datetime:
    require(isinstance(value, str) and bool(value), f"invalid timestamp: {field}")
    require(
        RFC3339_PATTERN.fullmatch(value) is not None,
        f"timestamp must be complete RFC3339 with timezone: {field}",
    )
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValidationError(f"invalid timestamp: {field}={value!r}") from error
    require(parsed.tzinfo is not None, f"timestamp timezone is required: {field}")
    return parsed


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
    require(
        active.get("projectName") == history.get("projectName"),
        "active/history project name mismatch",
    )
    metadata = active.get("metadata")
    require(isinstance(metadata, dict), "active metadata must be an object")
    require(
        metadata.get("frameworkId") == "intent-context-governance",
        "invalid HubICG frameworkId",
    )
    created = parse_timestamp(active.get("createdAt"), "agentconfig.createdAt")
    updated = parse_timestamp(active.get("lastUpdated"), "agentconfig.lastUpdated")
    require(updated >= created, "agentconfig lastUpdated precedes createdAt")

    current = active.get("currentVersion")
    require(isinstance(current, int) and current > 0, "invalid currentVersion")
    require(history.get("currentVersion") == current, "active/history version mismatch")

    versions = history.get("versions")
    require(isinstance(versions, list) and versions, "empty version history")
    require(
        all(isinstance(entry, dict) for entry in versions),
        "version history contains a non-object entry",
    )
    numbers = [entry.get("version") for entry in versions]
    require(numbers == list(range(1, current + 1)), "version history is not contiguous")

    previous_timestamp: datetime | None = None
    for position, entry in enumerate(versions, start=1):
        require(entry.get("newVersion") == position, "invalid newVersion link")
        expected_previous = None if position == 1 else position - 1
        require(
            entry.get("previousVersion") == expected_previous,
            "invalid previousVersion link",
        )
        timestamp = parse_timestamp(
            entry.get("timestamp"), f"history.versions[{position - 1}].timestamp"
        )
        if previous_timestamp is not None:
            require(timestamp >= previous_timestamp, "history timestamps regress")
        previous_timestamp = timestamp

        snapshot_rel = entry.get("snapshotFile")
        require(isinstance(snapshot_rel, str), "snapshotFile is missing")
        require(
            snapshot_rel == f"history/v{position:04d}.json",
            "snapshotFile does not match its version",
        )
        snapshot_path = root / ".promptsConfig" / snapshot_rel
        snapshot = read_json(snapshot_path)
        require(snapshot.get("version") == position, "snapshot version mismatch")
        parse_timestamp(snapshot.get("createdAt"), f"{snapshot_rel}.createdAt")

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
    require(metadata.get("configId") == "hubicg-primary-context", "invalid configId")
    try:
        version = int(metadata["configVersion"])
    except (KeyError, ValueError) as error:
        raise ValidationError("invalid context configVersion") from error
    require(version > 0, "context version must be positive")
    parse_timestamp(metadata.get("lastUpdated"), "context.lastUpdated")

    required_phrases = (
        "Já existe um repositório correspondente no GitHub",
        "Autoriza iniciar a migração da documentação",
        "pull apenas fast-forward",
        "Principal AI/ML Engineer",
        "Principal DevOps Engineer",
        "Não presuma organização, owner",
    )
    for phrase in required_phrases:
        require(phrase in text, f"context rule missing: {phrase}")
    return version


def validate_role_library(root: Path) -> int:
    library = root / ".promptsLibrary" / "role-prompts-ti-senior.md"
    manifest = root / ".promptsLibrary" / "MANIFEST.sha256"
    index_path = root / ".promptsLibrary" / "role-index.json"
    index = read_json(index_path)

    require(library.is_file(), "role library is missing")
    require(manifest.is_file(), "role library manifest is missing")
    manifest_parts = manifest.read_text(encoding="utf-8").split()
    require(len(manifest_parts) == 2, "invalid role library manifest")
    require(
        manifest_parts[1] == ".promptsLibrary/role-prompts-ti-senior.md",
        "manifest points to a different role library",
    )
    actual_hash = hashlib.sha256(library.read_bytes()).hexdigest()
    require(actual_hash == manifest_parts[0], "role library checksum mismatch")

    roles = index.get("roles")
    require(isinstance(roles, list) and len(roles) >= 60, "role index is incomplete")
    role_ids = [role.get("id") for role in roles if isinstance(role, dict)]
    role_names = [role.get("name") for role in roles if isinstance(role, dict)]
    require(len(role_ids) == len(roles), "role index contains a non-object entry")
    require(len(set(role_ids)) == len(role_ids), "duplicate role ids")
    require(len(set(role_names)) == len(role_names), "duplicate role names")
    require(
        "principal-multiformat-publishing-specialist" in role_ids,
        "multiformat publishing role is missing",
    )
    require("principal-git-engineer" in role_ids, "Git engineer role is missing")

    expected_index = build_index(library)
    require(index == expected_index, "role index is missing or stale")
    return len(roles)


def validate_prompt_histories(root: Path) -> int:
    files = sorted((root / ".promptsHistory").glob("*.json"))
    require(bool(files), "prompt history is empty")
    for path in files:
        data = read_json(path)
        require(bool(data.get("chatName")), f"chatName missing: {path}")
        created = parse_timestamp(data.get("createdAt"), f"{path}.createdAt")
        updated = parse_timestamp(data.get("lastUpdated"), f"{path}.lastUpdated")
        require(updated >= created, f"lastUpdated precedes createdAt: {path}")
        messages = data.get("messages")
        require(isinstance(messages, list), f"messages missing: {path}")
        previous = created
        for position, message in enumerate(messages):
            require(isinstance(message, dict), f"invalid message object: {path}")
            timestamp = parse_timestamp(
                message.get("timestamp"), f"{path}.messages[{position}].timestamp"
            )
            require(timestamp >= previous, f"messages are not chronological: {path}")
            require(timestamp <= updated, f"message is newer than lastUpdated: {path}")
            require(
                message.get("role") in MESSAGE_ROLES,
                f"invalid message role: {path}",
            )
            require(
                isinstance(message.get("content"), str),
                f"message content is not text: {path}",
            )
            previous = timestamp
    return len(files)


def main() -> None:
    default_root = os.environ.get(
        "HUBICG_REPO",
        os.environ.get("CODEX_CONFIG_REPO", str(DEFAULT_ROOT)),
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(default_root))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()

    try:
        schema_count, schema_instances = validate_all(root)
        agent_version = validate_snapshot_chain(root)
        context_version = validate_context(root)
        role_count = validate_role_library(root)
        history_count = validate_prompt_histories(root)
        require((root / "AGENTS.md").is_file(), "project AGENTS.md is missing")
        require(
            (root / "scripts" / "sync_codex_config.py").is_file(),
            "sync script is missing",
        )
    except (OSError, SchemaValidationError, ValidationError) as error:
        print(f"hubicg_config=invalid error={error}", file=sys.stderr)
        raise SystemExit(1)

    if not args.quiet:
        print(
            "hubicg_config=valid "
            f"agent_version={agent_version} "
            f"context_version={context_version} "
            f"roles={role_count} "
            f"prompt_histories={history_count} "
            f"schemas={schema_count} "
            f"schema_instances={schema_instances}"
        )


if __name__ == "__main__":
    main()
