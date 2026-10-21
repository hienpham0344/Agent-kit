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
        self.assertGreaterEqual(len(skill_files), 275, f"Expected at least 275 skills, found {len(skill_files)}")

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
        """Ensure all 22 agent profiles exist and are valid markdown files."""
        profiles = list((AGENTS_DIR / "profiles").glob("*.agent.md"))
        self.assertEqual(len(profiles), 22, f"Expected 22 agent profiles, found {len(profiles)}")

        for p in profiles:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(content.startswith("---"), f"{p.name} does not start with '---'")
            self.assertIn("name:", content, f"{p.name} missing name in frontmatter")
            self.assertIn("description:", content, f"{p.name} missing description in frontmatter")

    def test_workflow_recipes(self):
        """Ensure all 9 standard workflow recipes exist and are detailed."""
        recipes = list((WORKFLOWS_DIR / "recipes").glob("*.md"))
        self.assertEqual(len(recipes), 9, f"Expected 9 workflow recipes, found {len(recipes)}")
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
            "TICKET-TEMPLATE.md",
            "terraform-main.tf",
            "k6-load-script.js",
            "eval-prompt-matrix.yaml",
            "expo-app-config.json",
            "kubernetes-deployment.yaml"
        ]
        for t in required_templates:
            tmpl_path = WORKFLOWS_DIR / "templates" / t
            self.assertTrue(tmpl_path.exists(), f"Missing required template: {t}")

    def test_rules_exist(self):
        """Ensure core rule files exist."""
        self.assertTrue((RULES_DIR / "AGENTS.md").exists())
        self.assertTrue((RULES_DIR / "copilot-instructions.md").exists())
        self.assertTrue((AGENTS_DIR / "agents.toml").exists())

    def test_reference_guides(self):
        """Ensure reference guides exist and contain rich documentation."""
        ref_files = list((KIT_DIR / "references").glob("**/*.md"))
        self.assertGreaterEqual(len(ref_files), 6, f"Expected at least 6 reference guides, found {len(ref_files)}")
        for r in ref_files:
            self.assertGreater(r.stat().st_size, 400, f"{r.name} is too short or empty")

    def test_skills_json_manifest(self):
        """Ensure universal skills.json manifest exists and indexes all skills."""
        manifest_path = KIT_DIR / "skills.json"
        self.assertTrue(manifest_path.exists(), "skills.json manifest is missing")
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("skills", data)
        self.assertGreaterEqual(len(data["skills"]), 275)

if __name__ == "__main__":
    unittest.main()
