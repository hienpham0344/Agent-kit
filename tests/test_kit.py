#!/usr/bin/env python3
"""
Automated Test Suite for Agents-kit
Validates all 85 skills, 12 agent profiles, 5 workflows, and templates.
"""

import os
import sys
import unittest
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = KIT_DIR / "skills"
AGENTS_DIR = KIT_DIR / "agents"
WORKFLOWS_DIR = KIT_DIR / "workflows"
RULES_DIR = KIT_DIR / "rules"

class TestAgentsKit(unittest.TestCase):

    def test_skills_count_and_frontmatter(self):
        """Ensure all skills contain valid YAML frontmatter with name and description."""
        skill_files = list(SKILLS_DIR.glob("**/SKILL.md"))
        self.assertGreaterEqual(len(skill_files), 150, f"Expected at least 150 skills, found {len(skill_files)}")

        for s_file in skill_files:
            rel_path = s_file.relative_to(SKILLS_DIR)
            with open(s_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            self.assertTrue(content.startswith("---"), f"{rel_path} does not start with YAML frontmatter '---'")
            parts = content.split("---", 2)
            self.assertGreaterEqual(len(parts), 3, f"{rel_path} frontmatter is not closed with '---'")
            frontmatter = parts[1]
            self.assertIn("name:", frontmatter, f"{rel_path} missing 'name:' in frontmatter")
            self.assertIn("description:", frontmatter, f"{rel_path} missing 'description:' in frontmatter")

    def test_agent_profiles(self):
        """Ensure all 17 agent profiles exist and are valid markdown files."""
        profiles = list((AGENTS_DIR / "profiles").glob("*.agent.md"))
        self.assertEqual(len(profiles), 17, f"Expected 17 agent profiles, found {len(profiles)}")

        for p in profiles:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(content.startswith("---"), f"{p.name} does not start with '---'")
            self.assertIn("name:", content, f"{p.name} missing name in frontmatter")
            self.assertIn("description:", content, f"{p.name} missing description in frontmatter")

    def test_workflow_recipes(self):
        """Ensure all 5 standard workflow recipes exist and are detailed."""
        recipes = list((WORKFLOWS_DIR / "recipes").glob("*.md"))
        self.assertEqual(len(recipes), 5, f"Expected 5 workflow recipes, found {len(recipes)}")
        for r in recipes:
            self.assertGreater(r.stat().st_size, 500, f"{r.name} appears too small or empty")

    def test_production_templates(self):
        """Ensure critical templates exist."""
        required_templates = [
            "SRS-TEMPLATE.md",
            "DATABASE-SCHEMA-TEMPLATE.md",
            "DOCKERFILE-PATTERNS.md",
            "GITHUB-ACTIONS-WORKFLOW.md",
            "PR-TEMPLATE.md",
            "README-TEMPLATE.md",
            "PRINCIPLES-CHEAT-SHEET.md",
            "ADR-TEMPLATE.md",
            "GLOSSARY-TEMPLATE.md",
            "PLAN-TEMPLATE.md",
            "SPEC-TEMPLATE.md",
            "TICKET-TEMPLATE.md"
        ]
        for t in required_templates:
            tmpl_path = WORKFLOWS_DIR / "templates" / t
            self.assertTrue(tmpl_path.exists(), f"Missing required template: {t}")

    def test_rules_exist(self):
        """Ensure core rule files exist."""
        self.assertTrue((RULES_DIR / "AGENTS.md").exists())
        self.assertTrue((RULES_DIR / "copilot-instructions.md").exists())
        self.assertTrue((AGENTS_DIR / "agents.toml").exists())

if __name__ == "__main__":
    unittest.main()
