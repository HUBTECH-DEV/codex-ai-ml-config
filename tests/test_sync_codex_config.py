from __future__ import annotations

import importlib.util
import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTEXT = Path(".promptsConfig/codex-primary-context.md")


def run(
    *command: str,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode:
        raise AssertionError(
            f"command failed: {' '.join(command)}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


class SyncSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="hubicg-sync-test-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.remote = self.root / "remote.git"
        shutil.copytree(
            PROJECT_ROOT,
            self.repo,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        run("git", "init", "--initial-branch=main", str(self.repo), cwd=self.root)
        self.configure_identity(self.repo)
        run("git", "add", ".", cwd=self.repo)
        run("git", "commit", "-m", "baseline", cwd=self.repo)
        run("git", "init", "--bare", str(self.remote), cwd=self.root)
        run("git", "remote", "add", "origin", str(self.remote), cwd=self.repo)
        run("git", "push", "--set-upstream", "origin", "main", cwd=self.repo)
        self.baseline = self.rev_parse(self.repo, "HEAD")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def configure_identity(repo: Path) -> None:
        run("git", "config", "user.name", "HubICG Test", cwd=repo)
        run("git", "config", "user.email", "hubicg-test@example.invalid", cwd=repo)

    @staticmethod
    def rev_parse(repo: Path, ref: str) -> str:
        return run("git", "rev-parse", ref, cwd=repo).stdout.strip()

    def sync(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return run(
            sys.executable,
            "scripts/sync_codex_config.py",
            "--root",
            str(self.repo),
            *arguments,
            cwd=self.repo,
            check=check,
        )

    def append_context(self, text: str = "\nP0 sync test note.\n") -> None:
        path = self.repo / CONTEXT
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def remote_head(self) -> str:
        return run(
            "git",
            "--git-dir",
            str(self.remote),
            "rev-parse",
            "refs/heads/main",
            cwd=self.root,
        ).stdout.strip()

    def test_default_is_read_only_even_with_context_changes(self) -> None:
        self.append_context()
        before = (self.repo / CONTEXT).read_bytes()
        result = self.sync()
        self.assertIn("hubicg_sync=status", result.stdout)
        self.assertEqual(self.rev_parse(self.repo, "HEAD"), self.baseline)
        self.assertEqual(self.remote_head(), self.baseline)
        self.assertEqual((self.repo / CONTEXT).read_bytes(), before)

    def test_commit_is_explicit_and_scoped_to_context(self) -> None:
        self.append_context()
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8") + "\nlocal\n",
            encoding="utf-8",
        )
        result = self.sync("--commit")
        self.assertIn("hubicg_sync=committed", result.stdout)
        committed = run(
            "git",
            "show",
            "--format=",
            "--name-only",
            "HEAD",
            cwd=self.repo,
        ).stdout.split()
        self.assertEqual(committed, [CONTEXT.as_posix()])
        self.assertIn("README.md", run("git", "status", "--short", cwd=self.repo).stdout)
        self.assertEqual(self.remote_head(), self.baseline)

    def test_push_requires_a_separate_flag(self) -> None:
        self.append_context()
        self.sync("--commit")
        local = self.rev_parse(self.repo, "HEAD")
        self.assertNotEqual(local, self.baseline)
        self.assertEqual(self.remote_head(), self.baseline)
        result = self.sync("--push")
        self.assertIn("hubicg_sync=pushed", result.stdout)
        self.assertEqual(self.remote_head(), local)

    def test_push_blocks_commits_outside_context_scope(self) -> None:
        readme = self.repo / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8") + "\nunsafe scope\n",
            encoding="utf-8",
        )
        run("git", "add", "README.md", cwd=self.repo)
        run("git", "commit", "-m", "unrelated", cwd=self.repo)
        result = self.sync("--push", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the authorized context scope", result.stderr)
        self.assertEqual(self.remote_head(), self.baseline)

    def test_pull_is_explicit_and_fast_forward_only(self) -> None:
        writer = self.root / "writer"
        run(
            "git",
            "clone",
            "--branch",
            "main",
            str(self.remote),
            str(writer),
            cwd=self.root,
        )
        self.configure_identity(writer)
        readme = writer / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8") + "\nremote update\n",
            encoding="utf-8",
        )
        run("git", "add", "README.md", cwd=writer)
        run("git", "commit", "-m", "remote update", cwd=writer)
        run("git", "push", "origin", "main", cwd=writer)
        remote_commit = self.rev_parse(writer, "HEAD")

        self.sync()
        self.assertEqual(self.rev_parse(self.repo, "HEAD"), self.baseline)
        result = self.sync("--pull")
        self.assertIn("hubicg_sync=pulled", result.stdout)
        self.assertEqual(self.rev_parse(self.repo, "HEAD"), remote_commit)

    def test_mutation_is_blocked_on_detached_head(self) -> None:
        run("git", "checkout", "--detach", cwd=self.repo)
        result = self.sync("--fetch", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("detached HEAD", result.stderr)

    def test_commit_operates_in_a_real_linked_worktree(self) -> None:
        linked = self.root / "linked-worktree"
        run(
            "git",
            "worktree",
            "add",
            "-b",
            "linked-test",
            str(linked),
            cwd=self.repo,
        )
        self.assertTrue((linked / ".git").is_file())
        context = linked / CONTEXT
        context.write_text(
            context.read_text(encoding="utf-8") + "\nLinked worktree test.\n",
            encoding="utf-8",
        )
        result = run(
            sys.executable,
            "scripts/sync_codex_config.py",
            "--root",
            str(linked),
            "--branch",
            "linked-test",
            "--commit",
            cwd=linked,
        )
        self.assertIn("hubicg_sync=committed", result.stdout)
        committed = run(
            "git",
            "show",
            "--format=",
            "--name-only",
            "HEAD",
            cwd=linked,
        ).stdout.split()
        self.assertEqual(committed, [CONTEXT.as_posix()])

    def test_validation_archive_rejects_symbolic_links(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "hubicg_sync_module",
            PROJECT_ROOT / "scripts" / "sync_codex_config.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode="w:") as archive:
            member = tarfile.TarInfo("unsafe-link")
            member.type = tarfile.SYMTYPE
            member.linkname = "../../outside"
            archive.addfile(member)
        with tempfile.TemporaryDirectory(prefix="hubicg-tar-test-") as directory:
            with self.assertRaises(SystemExit):
                module.safe_extract_tar(payload.getvalue(), Path(directory))


if __name__ == "__main__":
    unittest.main()
