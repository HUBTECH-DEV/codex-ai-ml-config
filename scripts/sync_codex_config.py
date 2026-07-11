#!/usr/bin/env python3
"""Sincroniza o contexto primário do Codex com um repositório Git remoto."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

if os.name == "nt":
    import msvcrt
else:
    import fcntl


def fail(message: str) -> "NoReturn":
    print(f"ERRO: {message}", file=sys.stderr)
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
        fail(f"git {' '.join(args)} falhou: {detail}")
    return result


def output(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.strip()


def ref_exists(repo: Path, ref: str) -> bool:
    return git(repo, "show-ref", "--verify", "--quiet", ref, check=False).returncode == 0


def config_is_dirty(repo: Path, config_rel: str) -> bool:
    return bool(output(repo, "status", "--porcelain=v1", "--", config_rel))


def validate_staging_area(repo: Path, config_rel: str) -> None:
    staged = {
        path
        for path in output(repo, "diff", "--cached", "--name-only", "-z").split("\0")
        if path
    }
    unexpected = staged - {config_rel}
    if unexpected:
        fail(
            "há arquivos já staged fora do escopo: "
            + ", ".join(sorted(unexpected))
            + ". Limpe o índice antes de sincronizar."
        )


def bump_metadata(config_path: Path, tracked: bool) -> tuple[int, str]:
    text = config_path.read_text(encoding="utf-8")
    version_match = re.search(r"(?m)^configVersion:\s*(\d+)\s*$", text)
    updated_match = re.search(r'(?m)^lastUpdated:\s*"[^"]*"\s*$', text)
    if not version_match or not updated_match:
        fail("o arquivo [D] não contém configVersion e lastUpdated válidos")

    current_version = int(version_match.group(1))
    new_version = current_version + 1 if tracked else max(current_version, 1)
    timestamp = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    text = (
        text[: version_match.start(1)]
        + str(new_version)
        + text[version_match.end(1) :]
    )
    text = re.sub(
        r'(?m)^lastUpdated:\s*"[^"]*"\s*$',
        f'lastUpdated: "{timestamp}"',
        text,
        count=1,
    )
    config_path.write_text(text, encoding="utf-8")
    return new_version, timestamp


def require_identity(repo: Path) -> None:
    name = git(repo, "config", "--get", "user.name", check=False).stdout.strip()
    email = git(repo, "config", "--get", "user.email", check=False).stdout.strip()
    if not name:
        fail("configure git user.name antes do commit")
    if not email:
        fail("configure git user.email antes do commit")


@contextmanager
def repository_lock(path: Path) -> Iterator[None]:
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
            fail("outra sincronização já está em execução")

        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def main() -> None:
    script_repo = Path(__file__).resolve().parents[1]
    repo = Path(os.environ.get("CODEX_CONFIG_REPO", script_repo)).expanduser().resolve()
    config_rel = os.environ.get(
        "CODEX_CONFIG_FILE", ".promptsConfig/codex-primary-context.md"
    )
    remote = os.environ.get("CODEX_CONFIG_REMOTE", "origin")
    branch = os.environ.get("CODEX_CONFIG_BRANCH", "main")
    config_path = (repo / config_rel).resolve()

    if not (repo / ".git").exists():
        fail(f"{repo} não é um repositório Git")
    try:
        config_path.relative_to(repo)
    except ValueError:
        fail("CODEX_CONFIG_FILE deve permanecer dentro do repositório")
    if not config_path.is_file():
        fail(f"arquivo de configuração inexistente: {config_path}")

    lock_path = repo / ".git" / "codex-config-sync.lock"
    with repository_lock(lock_path):
        validate_staging_area(repo, config_rel)
        remote_url = output(repo, "remote", "get-url", remote)
        if not remote_url:
            fail(f"remoto {remote!r} não configurado")

        current_branch = output(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
        if current_branch != branch:
            fail(f"branch atual é {current_branch!r}; esperado {branch!r}")

        probe = git(repo, "ls-remote", remote, check=False)
        if probe.returncode:
            fail(f"remoto Git inacessível ou sem autenticação: {probe.stderr.strip()}")

        git(repo, "fetch", "--prune", remote)
        git(repo, "config", "pull.ff", "only")

        remote_ref = f"refs/remotes/{remote}/{branch}"
        remote_exists = ref_exists(repo, remote_ref)
        head_exists = git(
            repo, "rev-parse", "--verify", "--quiet", "HEAD", check=False
        ).returncode == 0
        dirty = config_is_dirty(repo, config_rel)

        ahead = behind = 0
        if head_exists and remote_exists:
            counts = output(repo, "rev-list", "--left-right", "--count", f"HEAD...{remote_ref}")
            ahead, behind = map(int, counts.split())

        if ahead and behind:
            fail(
                f"históricos divergiram (local +{ahead}, remoto +{behind}); "
                "resolva manualmente sem force push"
            )

        if behind:
            if dirty:
                fail(
                    "o remoto avançou e [D] possui alterações locais; "
                    "revise e integre manualmente"
                )
            git(repo, "pull", "--ff-only", remote, branch, capture=False)
            print(f"ATUALIZADO: [D] recebeu {behind} commit(s) do remoto.")
            return

        if dirty:
            tracked = (
                git(
                    repo,
                    "ls-files",
                    "--error-unmatch",
                    "--",
                    config_rel,
                    check=False,
                ).returncode
                == 0
            )
            require_identity(repo)
            version, timestamp = bump_metadata(config_path, tracked)
            git(repo, "add", "--", config_rel)
            if git(
                repo,
                "diff",
                "--cached",
                "--quiet",
                "--",
                config_rel,
                check=False,
            ).returncode == 0:
                print("SEM ALTERAÇÕES: conteúdo local já corresponde ao índice.")
                return
            git(
                repo,
                "commit",
                "-m",
                f"chore(prompts): atualiza contexto para v{version} ({timestamp})",
                "--",
                config_rel,
                capture=False,
            )
            ahead += 1

        if not head_exists and not dirty:
            fail("repositório sem commits e sem alteração local de [D]")

        if ahead or not remote_exists:
            git(repo, "push", "--set-upstream", remote, f"HEAD:{branch}", capture=False)
            print("PUBLICADO: baseline local de [D] enviado ao remoto.")
        else:
            print("SINCRONIZADO: versões local e remota de [D] são equivalentes.")


if __name__ == "__main__":
    main()
