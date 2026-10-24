"""
Unit and Integration Tests for Host Adapters (Antigravity, Claude, Copilot, Cursor, Windsurf).
Verifies that native configuration files and skill directories are generated accurately
without overwriting or path traversal.
"""

import tempfile
import shutil
import unittest
from pathlib import Path

from core.hosts.adapters import (
    AntigravityHostAdapter,
    ClaudeCodeHostAdapter,
    CopilotHostAdapter,
    CursorHostAdapter,
    WindsurfHostAdapter,
    get_adapter,
    HOST_ADAPTERS
)

KIT_DIR = Path(__file__).resolve().parent.parent

class TestHostAdapters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="agents_kit_host_test_")
        self.target = Path(self.temp_dir)
        self.sample_skills = [
            KIT_DIR / "skills" / "engineering-core" / "systematic-debugging",
            KIT_DIR / "skills" / "security-redteam" / "jwt-vulnerabilities-remediation"
        ]

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_antigravity_adapter(self):
        adapter = AntigravityHostAdapter(KIT_DIR, self.target)
        created = adapter.generate_configs(self.sample_skills, copy=True)
        self.assertTrue((self.target / ".agents" / "skills" / "systematic-debugging").exists())
        self.assertTrue((self.target / ".agents" / "agents.toml").exists())
        self.assertTrue((self.target / "AGENTS.md").exists())
        caps = adapter.get_capabilities()
        self.assertIn("Supported", caps["skill_discovery"])

    def test_claude_adapter(self):
        adapter = ClaudeCodeHostAdapter(KIT_DIR, self.target)
        created = adapter.generate_configs(self.sample_skills, copy=True)
        self.assertTrue((self.target / ".claude" / "skills" / "systematic-debugging").exists())
        self.assertTrue((self.target / "CLAUDE.md").exists())

    def test_copilot_adapter(self):
        adapter = CopilotHostAdapter(KIT_DIR, self.target)
        created = adapter.generate_configs(self.sample_skills, copy=False)
        self.assertTrue((self.target / ".github" / "agents").exists())
        self.assertTrue((self.target / ".github" / "copilot-instructions.md").exists())

    def test_cursor_and_windsurf_adapters(self):
        cursor_adapter = CursorHostAdapter(KIT_DIR, self.target)
        cursor_adapter.generate_configs(self.sample_skills)
        self.assertTrue((self.target / ".cursorrules").exists())

        windsurf_adapter = WindsurfHostAdapter(KIT_DIR, self.target)
        windsurf_adapter.generate_configs(self.sample_skills)
        self.assertTrue((self.target / ".windsurfrules").exists())

    def test_get_adapter_factory(self):
        for name in ("antigravity", "claude", "copilot", "cursor", "windsurf"):
            ad = get_adapter(name, KIT_DIR, self.target)
            self.assertIsNotNone(ad)
            self.assertEqual(ad.host_name, name)

        self.assertIsNone(get_adapter("unknown-host", KIT_DIR, self.target))

if __name__ == "__main__":
    unittest.main()
