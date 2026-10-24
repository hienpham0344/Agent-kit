"""
Tests for Skill Registry, Recommendation Engine, and Routing Accuracy.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from core.registry import SkillRegistry
from core.routing import SkillRouter

KIT_DIR = Path(__file__).resolve().parent.parent

class TestSkillRouting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry(KIT_DIR)
        cls.registry.load_catalog()
        cls.router = SkillRouter(KIT_DIR)

    def test_registry_indexes_all_285_skills(self):
        count = self.registry.get_total_count()
        self.assertEqual(count, 285)

        skill = self.registry.get_skill("systematic-debugging")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.category, "engineering-core")
        self.assertIn("debugging", skill.tags)

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

if __name__ == "__main__":
    unittest.main()
