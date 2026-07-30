from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.validate_schemas import SchemaValidationError, validate_datetime


ROOT = Path(__file__).resolve().parents[1]


class FrameworkValidationTests(unittest.TestCase):
    def run_script(self, relative: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / relative), *arguments],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

    def test_configuration_and_schemas_are_valid(self) -> None:
        for script in (
            "scripts/validate_schemas.py",
            "scripts/validate_codex_config.py",
        ):
            with self.subTest(script=script):
                result = self.run_script(script, "--root", str(ROOT))
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_role_index_is_deterministic(self) -> None:
        result = self.run_script("scripts/build_role_index.py", "--check")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_schema_datetime_rejects_date_only_or_timezone_free_values(self) -> None:
        for value in ("2026-07-30", "2026-07-30T13:14:24"):
            with self.subTest(value=value):
                with self.assertRaises(SchemaValidationError):
                    validate_datetime(value, "$.timestamp")

    def test_new_roles_are_indexed_in_their_own_section(self) -> None:
        data = json.loads(
            (ROOT / ".promptsLibrary" / "role-index.json").read_text(encoding="utf-8")
        )
        roles = {role["id"]: role for role in data["roles"]}
        self.assertEqual(len(roles), 60)
        expected_section = "Editoração Multiformato e Engenharia de Versionamento"
        self.assertEqual(
            roles["principal-multiformat-publishing-specialist"]["section"],
            expected_section,
        )
        self.assertEqual(
            roles["principal-git-engineer"]["section"],
            expected_section,
        )

    def test_multiformat_role_contains_approved_document_rules(self) -> None:
        text = (
            ROOT / ".promptsLibrary" / "role-prompts-ti-senior.md"
        ).read_text(encoding="utf-8")
        start = text.index("## Principal Multiformat Publishing Specialist")
        end = text.index("## Principal Git Engineer", start)
        role = text[start:end]
        required = (
            "web, impressão e leitura digital",
            "pergunte ao usuário",
            "documento novo",
            "metadados externos ao documento",
            "método pedagógico",
            "método editorial",
            "exclusivamente para referências",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, role)

    def test_preexisting_historical_files_are_byte_preserved(self) -> None:
        expected = {
            ".promptsConfig/history/v0001.json": (
                "22b562504ccb022517a1504be0f4b7c8680c75efe58f8870063095bdf1bc1ba5"
            ),
            ".promptsHistory/framework-bootstrap.json": (
                "8df5dae5d72e1bf1cbfd66169a7a526d8e6c3e4e5ab4e27c21bfc5b538a317ff"
            ),
        }
        for relative, digest in expected.items():
            with self.subTest(path=relative):
                actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(actual, digest)


if __name__ == "__main__":
    unittest.main()
