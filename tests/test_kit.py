#!/usr/bin/env python3
"""
Automated Test Suite for Agents-kit
Validates the skill catalog, agent profiles, workflows, and templates.
"""

import os
import re
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
        skill_files = list(SKILLS_DIR.glob("*/*/SKILL.md"))
        self.assertGreaterEqual(len(skill_files), 290, f"Expected at least 290 top-level skills, found {len(skill_files)}")

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

    def test_srs_skill_packages_are_self_contained(self):
        planning = SKILLS_DIR / "planning-grilling"
        spec_forge = planning / "spec-forge"
        problem_based = planning / "problem-based-srs"
        for required in (
            spec_forge / "SKILL.md",
            spec_forge / "skills" / "srs-generation" / "SKILL.md",
            spec_forge / "skills" / "srs-generation" / "references" / "template.md",
            spec_forge / "skills" / "shared" / "scripts" / "sf-trace.py",
            spec_forge / "LICENSE",
            problem_based / "SKILL.md",
            problem_based / "reference" / "functional-requirements.md",
            problem_based / "reference" / "validate.md",
            problem_based / "LICENSE",
        ):
            self.assertTrue(required.is_file(), f"Missing SRS skill asset: {required}")

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
        """Ensure all 10 standard workflow recipes exist and are detailed."""
        recipes = list((WORKFLOWS_DIR / "recipes").glob("*.md"))
        self.assertEqual(len(recipes), 10, f"Expected 10 workflow recipes, found {len(recipes)}")
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

    def test_frontend_skill_references_use_installed_path(self):
        frontend_skills = (SKILLS_DIR / "frontend-mastery").glob("*/SKILL.md")
        for skill_file in frontend_skills:
            content = skill_file.read_text(encoding="utf-8")
            self.assertNotIn("`references/frontend/", content, str(skill_file))
            for reference in re.findall(r"`docs/(references/frontend/[^`]+)`", content):
                self.assertTrue((KIT_DIR / reference).is_file(), reference)

    def test_skills_json_manifest(self):
        """Ensure universal skills.json manifest exists and indexes all skills."""
        manifest_path = KIT_DIR / "skills.json"
        self.assertTrue(manifest_path.exists(), "skills.json manifest is missing")
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("skills", data)
        top_level_count = len(list(SKILLS_DIR.glob("*/*/SKILL.md")))
        self.assertEqual(len(data["skills"]), top_level_count)
        self.assertGreaterEqual(len(data["skills"]), 290)

    def test_plugin_manifests_in_sync(self):
        """Ensure .claude-plugin/plugin.json and root plugin.json stay identical on core metadata."""
        import json
        root_plugin = json.loads((KIT_DIR / "plugin.json").read_text(encoding="utf-8"))
        claude_plugin = json.loads((KIT_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        for key in ("name", "version", "description", "repository"):
            self.assertEqual(root_plugin.get(key), claude_plugin.get(key), f"Drift in plugin.json field: {key}")

    def test_mcp_servers_no_hardcoded_user_paths(self):
        """Ensure mcp/servers.json uses portable placeholders rather than machine paths."""
        servers_text = (KIT_DIR / "mcp" / "servers.json").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"(/home/[^/\"'\s]+|/Users/[^/\"'\s]+)", servers_text))

    def test_skill_linter_passes_without_errors(self):
        from tools.skill_linter import lint_all_skills
        report = lint_all_skills(KIT_DIR)
        self.assertEqual(report["errors"], [], f"Skill linter errors: {report['errors']}")

    def test_cli_add_command(self):
        """Ensure the 'agents-kit add' command is functional."""
        import subprocess
        res = subprocess.run([str(KIT_DIR / "bin" / "agents-kit"), "add", "--help"], stdout=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Import skills from a GitHub repository", res.stdout)

    def test_doctor_does_not_claim_host_integration_is_verified(self):
        import subprocess
        res = subprocess.run([str(KIT_DIR / "bin" / "agents-kit"), "doctor"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Codex/MCP integration not checked", res.stdout)
        self.assertNotIn("100% HEALTHY", res.stdout)

if __name__ == "__main__":
    unittest.main()
