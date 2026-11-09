"""
Tests for Skill Registry, Recommendation Engine, and Routing Accuracy.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from core.registry import SkillRegistry
from core.routing import SkillRouter
from core.detection import detect_project_stack
from core.orchestration import OrchestrationEngine

KIT_DIR = Path(__file__).resolve().parent.parent

class TestSkillRouting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry(KIT_DIR)
        cls.registry.load_catalog()
        cls.router = SkillRouter(KIT_DIR)

    def test_registry_indexes_all_287_skills(self):
        count = self.registry.get_total_count()
        self.assertEqual(count, 287)

        skill = self.registry.get_skill("systematic-debugging")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.category, "engineering-core")
        self.assertIn("debugging", skill.tags)

    def test_registry_tags_match_words_not_substrings(self):
        self.assertNotIn("frontend", self.registry.get_skill("python-testing-patterns").tags)
        self.assertNotIn("frontend", self.registry.get_skill("design-patterns").tags)
        self.assertIn("frontend", self.registry.get_skill("frontend-ui-engineering").tags)

    def test_recommend_spring_boot_debugging(self):
        task = "Debug Java Spring Boot authentication failure with JWT tokens"
        res = self.router.recommend(task, top_k=5)
        self.assertGreater(len(res.recommendations), 0)

        top_names = [r.skill.name for r in res.recommendations]
        # Should recommend debugging and security/JWT skills
        self.assertTrue(
            any(name in top_names for name in ("systematic-debugging", "debugging-strategies", "jwt-vulnerabilities-remediation")),
            f"Expected debugging or jwt skills in top results, got: {top_names}"
        )
        # Check that reasons exist
        self.assertGreater(len(res.recommendations[0].reasons), 0)

    def test_recommend_react_frontend_animation(self):
        task = "Create smooth layout animations and drag and drop in React"
        res = self.router.recommend(task, top_k=5)
        top_names = [r.skill.name for r in res.recommendations]
        self.assertTrue(
            any(name in top_names for name in ("framer-motion-animation-patterns", "drag-and-drop-dndkit")),
            f"Expected animation or dnd skills, got: {top_names}"
        )

    def test_progressive_loading_level3_on_demand(self):
        content = self.registry.load_skill_content("systematic-debugging")
        self.assertIn("systematic-debugging", content)
        self.assertIn("root cause", content.lower())

    def test_nested_fullstack_project_is_detected_without_full_preset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text('{"scripts": {"test": "npm run test:frontend"}}')
            (root / "frontend").mkdir()
            (root / "frontend" / "package.json").write_text('{"dependencies": {"react": "^19"}}')
            (root / "backend").mkdir()
            (root / "backend" / "pom.xml").write_text("<project/>")

            result = detect_project_stack(root)

        self.assertIn("frontend", result.detected_languages)
        self.assertIn("java", result.detected_languages)
        self.assertIn("react", result.frameworks)
        self.assertEqual(result.recommended_preset, "fullstack")

    def test_recommend_react_dashboard_without_unrelated_specialties(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "frontend").mkdir()
            (root / "frontend" / "package.json").write_text('{"dependencies": {"react": "^19"}}')
            (root / "backend").mkdir()
            (root / "backend" / "pom.xml").write_text("<project/>")
            result = self.router.recommend("Xây giao diện dashboard React responsive", target_dir=root, top_k=5)
        names = [item.skill.name for item in result.recommendations]
        self.assertIn("frontend-ui-engineering", names)
        self.assertNotIn("resend-react-email", names)
        self.assertNotIn("react-native-expo-architecture", names)
        self.assertNotIn("react-hook-form-zod", names)
        self.assertNotIn("python-testing-patterns", names)
        self.assertNotIn("design-patterns", names)

    def test_recommend_spring_login_bug_without_unrelated_specialties(self):
        result = self.router.recommend("Sửa lỗi API đăng nhập Spring Boot", top_k=5)
        names = [item.skill.name for item in result.recommendations]
        self.assertIn("systematic-debugging", names)
        self.assertNotIn("api-gateway-auth0-cognito", names)
        self.assertNotIn("memory-leak-detection", names)

    def test_plan_uses_project_test_command_and_no_debugging_on_feature(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "package.json").write_text('{"scripts": {"test": "npm run test:frontend"}}')
            plan = OrchestrationEngine(KIT_DIR).decompose_task(
                "Build a React dashboard",
                selected_skills=["frontend-ui-engineering"],
                project_dir=root,
            )

        self.assertEqual(plan.steps[0].required_skills, [])
        self.assertEqual(plan.steps[1].verification_command, "npm test")

if __name__ == "__main__":
    unittest.main()
