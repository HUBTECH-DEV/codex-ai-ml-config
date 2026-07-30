#!/usr/bin/env python3
"""Inspect and explicitly synchronize the HubICG primary context.

With no action flag this command is read-only. Fetch, pull, commit and push are
independent operations and each requires its own explicit flag.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, NoReturn

if os.name == "nt":
    import msvcrt
else:
    import fcntl


def fail(message: str) -> NoReturn:
    print(f"hubicg_sync=blocked error={message}", file=sys.stderr)
    raise SystemExit(1)


def git(
    repo: Path,
    *args: str,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        capture_output=capture,
    )
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        fail(f"git {' '.join(args)} failed: {detail}")
    return result


def git_bytes(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).decode(errors="replace").strip()
        fail(f"git {' '.join(args)} failed: {detail}")
    return result


def output(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.strip()


def ref_exists(repo: Path, ref: str) -> bool:
    return git(repo, "show-ref", "--verify", "--quiet", ref, check=False).returncode == 0


def require_repository(repo: Path) -> None:
    probe = git(repo, "rev-parse", "--is-inside-work-tree", check=False)
    if probe.returncode or probe.stdout.strip() != "true":
        fail(f"{repo} is not a Git worktree")


def resolve_inside_repository(repo: Path, relative: str) -> Path:
    candidate = (repo / relative).resolve()
    try:
        candidate.relative_to(repo)
    except ValueError:
        fail("the configured context file must remain inside the repository")
    return candidate


def current_branch(repo: Path) -> str:
    return git(
        repo,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
        check=False,
    ).stdout.strip()


def require_branch(repo: Path, expected: str) -> None:
    current = current_branch(repo)
    if not current:
        fail("mutating actions are unavailable on a detached HEAD")
    if current != expected:
        fail(f"current branch is {current!r}; expected {expected!r}")


def require_remote(repo: Path, remote: str) -> str:
    result = git(repo, "remote", "get-url", remote, check=False)
    if result.returncode or not result.stdout.strip():
        fail(f"remote {remote!r} is not configured")
    return result.stdout.strip()


def relationship(repo: Path, remote_ref: str) -> tuple[int, int]:
    if not ref_exists(repo, remote_ref):
        return 0, 0
    counts = output(
        repo,
        "rev-list",
        "--left-right",
        "--count",
        f"HEAD...{remote_ref}",
    )
    ahead, behind = map(int, counts.split())
    return ahead, behind


def validate_framework(repo: Path, validator_source: Path | None = None) -> None:
    validator_root = validator_source or repo
    validator = validator_root / "scripts" / "validate_codex_config.py"
    if not validator.is_file():
        fail(f"validator is missing: {validator}")
    result = subprocess.run(
        [
            sys.executable,
            str(validator),
            "--root",
            str(repo),
            "--quiet",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        fail(
            "local validation failed before synchronization: "
            + (result.stderr or result.stdout).strip()
        )


def safe_extract_tar(payload: bytes, destination: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        root = destination.resolve()
        for member in archive.getmembers():
            if member.issym() or member.islnk():
                fail(f"links are not allowed in validation archives: {member.name}")
            target = (destination / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                fail(f"unsafe path in Git archive: {member.name}")
        archive.extractall(destination)


def validate_ref(repo: Path, ref: str) -> None:
    archive = git_bytes(repo, "archive", "--format=tar", ref).stdout
    with tempfile.TemporaryDirectory(prefix="hubicg-ref-") as directory:
        export = Path(directory)
        safe_extract_tar(archive, export)
        # Validate untrusted remote content with the already validated local
        # validator, not with code supplied by the remote ref.
        validate_framework(export, validator_source=repo)


def fetch_branch(repo: Path, remote: str, branch: str) -> str:
    require_remote(repo, remote)
    destination = f"refs/remotes/{remote}/{branch}"
    git(
        repo,
        "fetch",
        "--no-tags",
        remote,
        f"refs/heads/{branch}:{destination}",
        capture=False,
    )
    if not ref_exists(repo, destination):
        fail(f"remote branch {remote}/{branch} was not found")
    return destination


def require_clean_worktree(repo: Path) -> None:
    dirty = output(repo, "status", "--porcelain=v1")
    if dirty:
        fail("pull requires a completely clean worktree")


def staged_paths(repo: Path) -> set[str]:
    return {
        path
        for path in output(repo, "diff", "--cached", "--name-only", "-z").split("\0")
        if path
    }


def require_identity(repo: Path) -> None:
    name = git(repo, "config", "--get", "user.name", check=False).stdout.strip()
    email = git(repo, "config", "--get", "user.email", check=False).stdout.strip()
    if not name or not email:
        fail("configure git user.name and git user.email before --commit")


def bump_metadata(config_path: Path) -> tuple[int, str]:
    text = config_path.read_text(encoding="utf-8")
    version_match = re.search(r"(?m)^configVersion:\s*(\d+)\s*$", text)
    updated_match = re.search(r'(?m)^lastUpdated:\s*"[^"]*"\s*$', text)
    if not version_match or not updated_match:
        fail("the primary context lacks valid configVersion/lastUpdated metadata")

    version = int(version_match.group(1)) + 1
    timestamp = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    text = (
        text[: version_match.start(1)]
        + str(version)
        + text[version_match.end(1) :]
    )
    text = re.sub(
        r'(?m)^lastUpdated:\s*"[^"]*"\s*$',
        f'lastUpdated: "{timestamp}"',
        text,
        count=1,
    )
    config_path.write_text(text, encoding="utf-8")
    return version, timestamp


def restore_failed_commit(
    repo: Path,
    config_path: Path,
    config_rel: str,
    original: str,
) -> None:
    config_path.write_text(original, encoding="utf-8")
    git(repo, "reset", "--quiet", "HEAD", "--", config_rel, check=False)


def commit_context(
    repo: Path,
    config_path: Path,
    config_rel: str,
    message: str | None,
) -> None:
    require_identity(repo)
    if staged_paths(repo):
        fail("--commit requires an empty staging area")
    tracked = git(
        repo,
        "ls-files",
        "--error-unmatch",
        "--",
        config_rel,
        check=False,
    )
    if tracked.returncode:
        fail(f"--commit only supports the tracked context file {config_rel!r}")
    if not output(repo, "status", "--porcelain=v1", "--", config_rel):
        fail(f"there are no context changes to commit: {config_rel}")

    original = config_path.read_text(encoding="utf-8")
    version, timestamp = bump_metadata(config_path)
    try:
        validate_framework(repo)
        git(repo, "add", "--", config_rel)
        commit_message = message or (
            f"chore(hubicg): update primary context to v{version} ({timestamp})"
        )
        git(
            repo,
            "commit",
            "--only",
            "-m",
            commit_message,
            "--",
            config_rel,
            capture=False,
        )
    except SystemExit:
        restore_failed_commit(repo, config_path, config_rel, original)
        raise

    validate_framework(repo)
    committed = {
        path
        for path in output(repo, "show", "--format=", "--name-only", "HEAD").splitlines()
        if path
    }
    if committed != {config_rel}:
        fail(f"created commit escaped the authorized scope: {sorted(committed)}")
    print(f"hubicg_sync=committed version={version} file={config_rel}")


def pull_fast_forward(repo: Path, remote: str, branch: str) -> None:
    require_clean_worktree(repo)
    remote_ref = fetch_branch(repo, remote, branch)
    ahead, behind = relationship(repo, remote_ref)
    if ahead and behind:
        fail(
            f"histories diverged (local +{ahead}, remote +{behind}); "
            "manual review is required"
        )
    if ahead:
        print(f"hubicg_sync=pull_skipped local_ahead={ahead}")
        return
    if not behind:
        print("hubicg_sync=pull_noop")
        return

    validate_ref(repo, remote_ref)
    git(repo, "merge", "--ff-only", remote_ref, capture=False)
    validate_framework(repo)
    print(f"hubicg_sync=pulled commits={behind}")


def ahead_paths(repo: Path, remote_ref: str) -> set[str]:
    return {
        path
        for path in output(
            repo,
            "log",
            "--format=",
            "--name-only",
            f"{remote_ref}..HEAD",
        ).splitlines()
        if path
    }


def push_context(repo: Path, remote: str, branch: str, config_rel: str) -> None:
    if output(repo, "status", "--porcelain=v1", "--", config_rel):
        fail("--push refuses an uncommitted primary context; use --commit separately")
    remote_ref = fetch_branch(repo, remote, branch)
    ahead, behind = relationship(repo, remote_ref)
    if ahead and behind:
        fail(
            f"histories diverged (local +{ahead}, remote +{behind}); "
            "manual review is required"
        )
    if behind:
        fail(f"local branch is behind by {behind}; authorize --pull separately")
    if not ahead:
        print("hubicg_sync=push_noop")
        return

    paths = ahead_paths(repo, remote_ref)
    unexpected = paths - {config_rel}
    if unexpected:
        fail(
            "outgoing commits contain files outside the authorized context scope: "
            + ", ".join(sorted(unexpected))
        )
    validate_framework(repo)
    git(
        repo,
        "push",
        remote,
        f"HEAD:refs/heads/{branch}",
        capture=False,
    )
    expected = output(repo, "rev-parse", "HEAD")
    published = output(repo, "ls-remote", remote, f"refs/heads/{branch}").split()
    if not published or published[0] != expected:
        fail("remote verification did not return the pushed commit")
    print(f"hubicg_sync=pushed commits={ahead} branch={branch}")


def common_git_dir(repo: Path) -> Path:
    value = Path(output(repo, "rev-parse", "--git-common-dir"))
    if not value.is_absolute():
        value = repo / value
    return value.resolve()


@contextmanager
def repository_lock(repo: Path) -> Iterator[None]:
    path = common_git_dir(repo) / "hubicg-sync.lock"
    with path.open("a+b") as lock:
        try:
            if os.name == "nt":
                lock.seek(0)
                if lock.read(1) == b"":
                    lock.write(b"\0")
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            fail("another HubICG synchronization action is running")
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def report_status(
    repo: Path,
    remote: str,
    branch: str,
    config_rel: str,
) -> None:
    current = current_branch(repo) or "(detached)"
    remote_ref = f"refs/remotes/{remote}/{branch}"
    ahead, behind = relationship(repo, remote_ref)
    dirty = bool(output(repo, "status", "--porcelain=v1", "--", config_rel))
    remote_url = git(repo, "remote", "get-url", remote, check=False).stdout.strip()
    print(
        "hubicg_sync=status "
        f"branch={current} expected_branch={branch} "
        f"context_dirty={str(dirty).lower()} "
        f"cached_ahead={ahead} cached_behind={behind} "
        f"remote_configured={str(bool(remote_url)).lower()}"
    )


def parse_args() -> argparse.Namespace:
    default_root = os.environ.get(
        "HUBICG_REPO",
        os.environ.get(
            "CODEX_CONFIG_REPO",
            str(Path(__file__).resolve().parents[1]),
        ),
    )
    parser = argparse.ArgumentParser(
        description=(
            "Inspect HubICG by default; authorize fetch, pull, commit and push "
            "with separate explicit flags."
        )
    )
    parser.add_argument("--root", type=Path, default=Path(default_root))
    parser.add_argument(
        "--config-file",
        default=os.environ.get(
            "HUBICG_CONFIG_FILE",
            os.environ.get(
                "CODEX_CONFIG_FILE",
                ".promptsConfig/codex-primary-context.md",
            ),
        ),
    )
    parser.add_argument(
        "--remote",
        default=os.environ.get(
            "HUBICG_REMOTE",
            os.environ.get("CODEX_CONFIG_REMOTE", "origin"),
        ),
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get(
            "HUBICG_BRANCH",
            os.environ.get("CODEX_CONFIG_BRANCH", "main"),
        ),
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="authorize updating the configured remote-tracking branch only",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="authorize fetch plus a clean-worktree fast-forward merge",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="authorize a local commit containing only the primary context",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="authorize pushing only context-only commits to the configured branch",
    )
    parser.add_argument(
        "--commit-message",
        help="optional commit message; valid only together with --commit",
    )
    args = parser.parse_args()
    if args.commit_message and not args.commit:
        parser.error("--commit-message requires --commit")
    return args


def main() -> None:
    args = parse_args()
    repo = args.root.expanduser().resolve()
    require_repository(repo)
    config_path = resolve_inside_repository(repo, args.config_file)
    if not config_path.is_file():
        fail(f"primary context does not exist: {config_path}")

    validate_framework(repo)
    actions = args.fetch or args.pull or args.commit or args.push
    if not actions:
        report_status(repo, args.remote, args.branch, args.config_file)
        return

    require_branch(repo, args.branch)
    with repository_lock(repo):
        if args.pull:
            pull_fast_forward(repo, args.remote, args.branch)
        elif args.fetch:
            fetch_branch(repo, args.remote, args.branch)
            print(f"hubicg_sync=fetched branch={args.remote}/{args.branch}")
        if args.commit:
            commit_context(
                repo,
                config_path,
                args.config_file,
                args.commit_message,
            )
        if args.push:
            push_context(repo, args.remote, args.branch, args.config_file)
    report_status(repo, args.remote, args.branch, args.config_file)


if __name__ == "__main__":
    main()
