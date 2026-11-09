"""Regression tests for project installation diagnostics."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from core.manifest import ManifestManager


KIT_DIR = Path(__file__).resolve().parent.parent
CLI = KIT_DIR / "bin" / "agents-kit"


class TestDoctor(unittest.TestCase):
    def run_doctor(self, project: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(CLI), "doctor", "--project", str(project)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_uninstalled_project_is_detected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_doctor(Path(temp_dir))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("UNINSTALLED", result.stdout)
        self.assertIn("install", result.stdout)
        self.assertIn("--dry-run", result.stdout)

    def test_unmanaged_skills_are_not_called_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            active = project / ".agents" / "skills"
            active.mkdir(parents=True)
            (active / "systematic-debugging").symlink_to(
                KIT_DIR / "skills" / "engineering-core" / "systematic-debugging",
                target_is_directory=True,
            )
            result = self.run_doctor(project)
        self.assertIn("UNMANAGED", result.stdout)
        self.assertIn("1 active", result.stdout)
        self.assertNotIn("UNINSTALLED", result.stdout)

    def test_managed_install_detects_broken_skill_and_modified_rule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            active = project / ".agents" / "skills"
            active.mkdir(parents=True)
            (active / "systematic-debugging").symlink_to(
                project / "missing-skill", target_is_directory=True
            )
            rule = project / "AGENTS.md"
            rule.write_text("original", encoding="utf-8")
            ManifestManager(project).save_manifest(
                preset="minimal", mode="symlink", categories=["engineering-core"],
                installed_skills=["systematic-debugging"], managed_files=["AGENTS.md"],
            )
            rule.write_text("user edit", encoding="utf-8")
            result = self.run_doctor(project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BROKEN", result.stdout)
        self.assertIn("systematic-debugging", result.stdout)
        self.assertIn("MODIFIED", result.stdout)
        self.assertIn("AGENTS.md", result.stdout)

    def test_managed_install_recognizes_valid_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            active = project / ".agents" / "skills"
            active.mkdir(parents=True)
            (active / "systematic-debugging").symlink_to(
                KIT_DIR / "skills" / "engineering-core" / "systematic-debugging",
                target_is_directory=True,
            )
            ManifestManager(project).save_manifest(
                preset="minimal", mode="symlink", categories=["engineering-core"],
                installed_skills=["systematic-debugging"], managed_files=[],
            )
            result = self.run_doctor(project)
        self.assertEqual(result.returncode, 0)
        self.assertIn("MANAGED", result.stdout)
        self.assertIn("1 active", result.stdout)

    def test_invalid_manifest_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            manifest = project / ".agents" / "agents-kit.manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{invalid", encoding="utf-8")
            result = self.run_doctor(project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("INVALID", result.stdout)

    def test_manifest_path_outside_project_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            ManifestManager(project).save_manifest(
                preset="minimal", mode="symlink", categories=[],
                installed_skills=[], managed_files={"../outside.txt": "hash"},
            )
            result = self.run_doctor(project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("INVALID managed path", result.stdout)

    def test_empty_managed_skill_list_is_incomplete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            active = project / ".agents" / "skills"
            active.mkdir(parents=True)
            (active / "systematic-debugging").symlink_to(
                KIT_DIR / "skills" / "engineering-core" / "systematic-debugging",
                target_is_directory=True,
            )
            ManifestManager(project).save_manifest(
                preset="minimal", mode="symlink", categories=["engineering-core"],
                installed_skills=[], managed_files=[],
            )
            result = self.run_doctor(project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("INCOMPLETE", result.stdout)


if __name__ == "__main__":
    unittest.main()
