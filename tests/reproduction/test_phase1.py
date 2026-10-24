"""
Reproduction and regression tests for Phase 1 P0/P1 bugs.
These tests verify that the old bugs fail and new fixes pass.
"""

import os
import sys
import tempfile
import unittest
import shutil
import subprocess
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(KIT_DIR))

class TestPhase1Reproduction(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="agents_kit_test_")
        self.target = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_p0_project_stack_detection_not_always_full(self):
        """Auto-detection must not return 'full' on empty or single-stack projects."""
        from core.detection import detect_project_stack

        # 1. Empty directory should be minimal/general, definitely not full
        res_empty = detect_project_stack(self.target)
        self.assertNotEqual(res_empty.recommended_preset, "full")
        self.assertEqual(res_empty.recommended_preset, "minimal")

        # 2. Python-only project
        (self.target / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
        res_py = detect_project_stack(self.target)
        self.assertIn("python", res_py.detected_languages)
        self.assertIn("stacks", res_py.recommended_categories)
        self.assertEqual(res_py.recommended_preset, "backend")

        # 3. Java Maven project
        (self.target / "pyproject.toml").unlink()
        (self.target / "pom.xml").write_text("<project></project>", encoding="utf-8")
        res_java = detect_project_stack(self.target)
        self.assertIn("java", res_java.detected_languages)
        self.assertIn("stacks", res_java.recommended_categories)

        # 4. React Frontend project
        (self.target / "pom.xml").unlink()
        (self.target / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}', encoding="utf-8")
        res_react = detect_project_stack(self.target)
        self.assertIn("react", res_react.frameworks)
        self.assertEqual(res_react.recommended_preset, "web")

    def test_p1_presets_consistency(self):
        """Ensure all categories in PRESETS actually exist in the skills/ directory."""
        from core.presets import PRESETS
        skills_dir = KIT_DIR / "skills"
        existing_cats = {d.name for d in skills_dir.iterdir() if d.is_dir()}

        for preset_name, cats in PRESETS.items():
            for c in cats:
                self.assertIn(c, existing_cats, f"Preset '{preset_name}' references non-existent category '{c}'")

        # Verify devops has cloud categories as promised in README
        self.assertIn("cloud-infra", PRESETS["devops"])
        self.assertIn("sre-observability", PRESETS["devops"])
        self.assertIn("cloud-aws-gcp-azure", PRESETS["devops"])

        # Verify security has security-redteam
        self.assertIn("security-redteam", PRESETS["security"])

    def test_p0_prevent_destructive_install_on_user_custom_skills(self):
        """Install must not delete user's custom skill or unmanaged files without confirmation."""
        from core.planner import InstallationPlanner

        # User has an existing skill in .agents/skills/my-custom-skill
        user_skill = self.target / ".agents" / "skills" / "my-custom-skill"
        user_skill.mkdir(parents=True, exist_ok=True)
        (user_skill / "SKILL.md").write_text("user custom content", encoding="utf-8")

        # User customized AGENTS.md
        user_agents_md = self.target / "AGENTS.md"
        user_agents_md.write_text("# My Custom User Agents Config", encoding="utf-8")

        planner = InstallationPlanner(kit_dir=KIT_DIR, target_dir=self.target, preset="minimal", copy=False)
        plan = planner.plan()

        # Custom skill must not be touched or deleted
        self.assertTrue(user_skill.exists())
        self.assertEqual(len([op for op in plan.operations if "my-custom-skill" in str(op.dst)]), 0)

        # AGENTS.md conflict must be detected
        conflicts = [op for op in plan.operations if op.dst.name == "AGENTS.md" and op.is_conflict]
        self.assertEqual(len(conflicts), 1)

    def test_p0_sync_preserves_previous_preset_and_mode(self):
        """Sync must respect target project's manifest and not force full symlink."""
        from core.manifest import ManifestManager
        from core.planner import InstallationPlanner

        manifest_mgr = ManifestManager(self.target)
        manifest_mgr.save_manifest(
            preset="web",
            mode="copy",
            categories=["frontend-mastery", "design-uiux"],
            installed_skills=["fluid-typography-spacing"],
            managed_files=["AGENTS.md"]
        )

        manifest = manifest_mgr.load_manifest()
        self.assertEqual(manifest.preset, "web")
        self.assertEqual(manifest.mode, "copy")
        self.assertIn("fluid-typography-spacing", manifest.installed_skills)

    def test_p0_security_path_traversal_on_import(self):
        """Importing skill with malicious name like '../../etc/cron' must raise SecurityError."""
        from core.security import validate_skill_name, validate_safe_destination

        with self.assertRaises(ValueError):
            validate_skill_name("../../etc/cron")

        with self.assertRaises(ValueError):
            validate_skill_name("/etc/passwd")

        with self.assertRaises(ValueError):
            validate_safe_destination(self.target / ".agents" / "skills", self.target / ".." / "outside")

    def test_p0_subprocess_exit_code_propagation(self):
        """CLI wrapper must propagate non-zero exit codes from child subprocesses."""
        from core.cli import safe_run_subprocess

        code = safe_run_subprocess([sys.executable, "-c", "import sys; sys.exit(42)"])
        self.assertEqual(code, 42)

if __name__ == "__main__":
    unittest.main()
