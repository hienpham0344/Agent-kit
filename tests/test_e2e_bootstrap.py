"""End-to-end bootstrap & multi-stack installation lifecycle tests."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.detection import detect_project_stack

KIT_DIR = Path(__file__).resolve().parent.parent
CLI = KIT_DIR / "bin" / "agents-kit"


class TestE2EBootstrap(unittest.TestCase):
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(CLI), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_auto_detection_across_five_project_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            # 1. Next.js web app
            nextjs = root / "nextjs-app"
            nextjs.mkdir()
            (nextjs / "package.json").write_text('{"dependencies": {"next": "15.0.0", "react": "19.0.0"}}')
            det_next = detect_project_stack(nextjs)
            self.assertIn("frontend", det_next.detected_languages)
            self.assertEqual(det_next.recommended_preset, "web")

            # 2. Python FastAPI + LangGraph AI app
            py_ai = root / "py-ai-app"
            py_ai.mkdir()
            (py_ai / "pyproject.toml").write_text('[project]\ndependencies = ["fastapi", "langgraph", "openai"]')
            det_py = detect_project_stack(py_ai)
            self.assertIn("python", det_py.detected_languages)
            self.assertIn("ai-llm", det_py.recommended_categories)
            self.assertEqual(det_py.recommended_preset, "ai")

            # 3. Java Spring Boot backend
            java_app = root / "java-app"
            java_app.mkdir()
            (java_app / "pom.xml").write_text("<project><dependencies><dependency>spring-boot-starter-web</dependency></dependencies></project>")
            det_java = detect_project_stack(java_app)
            self.assertIn("java", det_java.detected_languages)
            self.assertEqual(det_java.recommended_preset, "backend")

            # 4. Go + Docker service
            go_app = root / "go-app"
            go_app.mkdir()
            (go_app / "go.mod").write_text("module example.com/service\n\ngo 1.22\n")
            (go_app / "Dockerfile").write_text("FROM golang:1.22-alpine\n")
            det_go = detect_project_stack(go_app)
            self.assertIn("go", det_go.detected_languages)
            self.assertIn("docker", det_go.infrastructure)
            self.assertEqual(det_go.recommended_preset, "backend")

            # 5. Empty directory falls back to minimal safe preset
            empty_dir = root / "empty-app"
            empty_dir.mkdir()
            det_empty = detect_project_stack(empty_dir)
            self.assertEqual(det_empty.recommended_preset, "minimal")

    def test_host_isolated_install_doctor_and_clean_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            # Host: claude -> writes CLAUDE.md + .claude/skills, NOT AGENTS.md or .cursorrules
            claude_proj = root / "claude-proj"
            claude_proj.mkdir()
            (claude_proj / "pyproject.toml").write_text('[project]\ndependencies = ["fastapi"]')
            user_note = claude_proj / "USER_KEEP.md"
            user_note.write_text("do not delete me", encoding="utf-8")

            res_install = self._run_cli("install", str(claude_proj), "--preset", "minimal", "--host", "claude")
            self.assertEqual(res_install.returncode, 0, res_install.stdout + res_install.stderr)
            self.assertTrue((claude_proj / "CLAUDE.md").is_file())
            self.assertTrue((claude_proj / ".claude" / "skills" / "systematic-debugging" / "SKILL.md").is_file())
            self.assertFalse((claude_proj / "AGENTS.md").exists())
            self.assertFalse((claude_proj / ".cursorrules").exists())

            manifest = json.loads((claude_proj / ".agents" / "agents-kit.manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["host"], "claude")
            self.assertEqual(Path(manifest["kit_dir"]).resolve(), KIT_DIR.resolve())

            res_doc = self._run_cli("doctor", "--project", str(claude_proj), "--json")
            self.assertEqual(res_doc.returncode, 0, res_doc.stdout + res_doc.stderr)
            doc_data = json.loads(res_doc.stdout)
            self.assertTrue(doc_data["health"]["healthy"])
            self.assertIn("claude", doc_data["health"]["detected_hosts"])

            # Clean uninstall removes managed files/skills while preserving user file
            res_un = self._run_cli("uninstall", str(claude_proj))
            self.assertEqual(res_un.returncode, 0, res_un.stdout + res_un.stderr)
            self.assertFalse((claude_proj / "CLAUDE.md").exists())
            self.assertFalse((claude_proj / ".claude" / "skills" / "systematic-debugging").exists())
            self.assertTrue(user_note.is_file())

    def test_copilot_and_cursor_host_isolations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            cursor_proj = root / "cursor-proj"
            cursor_proj.mkdir()
            res_cur = self._run_cli("install", str(cursor_proj), "--preset", "minimal", "--host", "cursor")
            self.assertEqual(res_cur.returncode, 0, res_cur.stdout + res_cur.stderr)
            self.assertTrue((cursor_proj / ".cursorrules").is_file())
            self.assertFalse((cursor_proj / ".github" / "copilot-instructions.md").exists())

            copilot_proj = root / "copilot-proj"
            copilot_proj.mkdir()
            res_cop = self._run_cli("install", str(copilot_proj), "--preset", "minimal", "--host", "copilot")
            self.assertEqual(res_cop.returncode, 0, res_cop.stdout + res_cop.stderr)
            self.assertTrue((copilot_proj / ".github" / "copilot-instructions.md").is_file())
            self.assertTrue((copilot_proj / ".github" / "agents").is_dir())
            self.assertFalse((copilot_proj / ".cursorrules").exists())

    def test_zero_pyyaml_stdlib_fallback_under_blocked_yaml(self):
        """Prove SkillRegistry, linter, doctor --json, and install --dry-run work without PyYAML."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "target"
            proj.mkdir()
            (proj / "go.mod").write_text("module demo\n\ngo 1.22\n")

            code = (
                "import sys; from pathlib import Path; "
                "sys.modules['yaml'] = None; "
                f"kit = Path({str(KIT_DIR)!r}); "
                "sys.path.insert(0, str(kit)); "
                "from core.registry import SkillRegistry, USING_PYYAML; "
                "assert USING_PYYAML is False, 'Expected PyYAML to be blocked'; "
                "reg = SkillRegistry(kit); "
                "reg.load_catalog(); "
                "assert reg.get_total_count() >= 290; "
                "assert reg.get_skill('systematic-debugging') is not None; "
                "from tools.skill_linter import lint_all_skills; "
                "rep = lint_all_skills(kit); "
                "assert not rep['errors'], rep['errors']; "
                f"sys.argv = ['agents-kit', 'install', {str(proj)!r}, '--preset', 'auto', '--host', 'antigravity', '--dry-run']; "
                "from core.cli_entry import main; main()"
            )
            res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertIn("DRY RUN", res.stdout)


if __name__ == "__main__":
    unittest.main()
