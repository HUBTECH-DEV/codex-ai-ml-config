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
                "c1f3c714be6ff5f1cd65ce63935799445a4ea69da68647a34bc2623be88f0b4d"
            ),
            ".promptsConfig/history/v0002.json": (
                "817e0280c3f6169dfe1b88ac62dcec5c9c0c62be58ad276bab60f05176591d79"
            ),
            ".promptsConfig/history/v0003.json": (
                "db9e7df57e9eb769324bf8c49abd3dcbfc1cc3acfb8f5b171da8c64e43f2cd92"
            ),
            ".promptsHistory/framework-bootstrap.json": (
                "f42fa61363a33b92b5b6d464be98ad05ec02fe5f0b1d860eb93016cd54c8cb2c"
            ),
            ".promptsHistory/ai-ml-beta-project-setup.json": (
                "695889f46d2297e90807baf80a4f5d670ed87ffb1a2c95284f86967c77bd12ae"
            ),
            ".promptsHistory/github-migration-audit.json": (
                "7b9d20ced46e9e97993b2fc9d8515b2b974b4748d018ad468b9d51ec20660938"
            ),
            "docs/releases/beta-v0.2.0.md": (
                "d4150680ae93d61772c556d9eb73069863cd9d0972f62b57b6e3d8ba852c4183"
            ),
        }
        for relative, digest in expected.items():
            with self.subTest(path=relative):
                actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(actual, digest)


if __name__ == "__main__":
    unittest.main()
