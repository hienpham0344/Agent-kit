"""Regression tests for safe installation and manifest accounting."""

import tempfile
import unittest
import subprocess
from pathlib import Path

from core.manifest import ManifestManager
from core.planner import InstallationPlanner


KIT_DIR = Path(__file__).resolve().parent.parent


class TestInstallation(unittest.TestCase):
    def test_cli_backup_dry_run_accepts_conflict_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            rule = target / "AGENTS.md"
            rule.write_text("user instructions", encoding="utf-8")
            result = subprocess.run(
                [str(KIT_DIR / "bin" / "agents-kit"), "install", str(target),
                 "--preset", "minimal", "--backup", "--dry-run"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(rule.read_text(encoding="utf-8"), "user instructions")
            self.assertFalse((target / ".agents" / "agents-kit.manifest.json").exists())

    def test_sync_without_backup_preserves_unmanaged_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            rule = target / "AGENTS.md"
            rule.write_text("user instructions", encoding="utf-8")
            result = subprocess.run(
                [str(KIT_DIR / "bin" / "agents-kit"), "sync", str(target)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(rule.read_text(encoding="utf-8"), "user instructions")

    def test_backup_allows_conflicting_rules_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            rule = target / "AGENTS.md"
            rule.write_text("user instructions", encoding="utf-8")
            planner = InstallationPlanner(KIT_DIR, target, preset="minimal", backup=True)
            plan = planner.plan()
            self.assertTrue(plan.has_conflicts)
            result = planner.execute(plan)
            backups = list((target / ".agents" / "backups").glob("*/AGENTS.md"))
            self.assertEqual(result["backed_up"], 1)
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "user instructions")
            self.assertIn("Automatic Skill and Subagent Routing", rule.read_text(encoding="utf-8"))

    def test_unchanged_skill_remains_in_manifest_after_sync(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            planner = InstallationPlanner(KIT_DIR, target, preset="minimal")
            planner.execute(planner.plan())
            before = ManifestManager(target).load_manifest()
            self.assertTrue(before.installed_skills)
            second = InstallationPlanner(KIT_DIR, target, preset="minimal")
            second.execute(second.plan())
            after = ManifestManager(target).load_manifest()
            self.assertEqual(set(after.installed_skills), set(before.installed_skills))


if __name__ == "__main__":
    unittest.main()
