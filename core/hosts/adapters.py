"""
Native Host Adapters for AI Coding Environments.
Converts canonical Agent-kit skills and agent profiles into verified, native host formats:
- Google Antigravity: .agents/skills/, .agents/agents.toml, AGENTS.md
- Claude Code: .claude/skills/, .claude/agents/, CLAUDE.md
- GitHub Copilot / VS Code: .github/agents/*.agent.md, .github/copilot-instructions.md
- Cursor: .cursorrules
- Windsurf: .windsurfrules
"""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional

class BaseHostAdapter(ABC):
    def __init__(self, kit_dir: Path, target_dir: Path):
        self.kit_dir = kit_dir.resolve()
        self.target_dir = target_dir.resolve()

    @property
    @abstractmethod
    def host_name(self) -> str:
        pass

    @abstractmethod
    def generate_configs(self, skills: List[Path], copy: bool = False) -> List[str]:
        """Generate native configurations and return list of created file paths."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, str]:
        """Return host capability matrix status."""
        pass

class AntigravityHostAdapter(BaseHostAdapter):
    @property
    def host_name(self) -> str:
        return "antigravity"

    def generate_configs(self, skills: List[Path], copy: bool = False) -> List[str]:
        created = []
        skills_dest = self.target_dir / ".agents" / "skills"
        skills_dest.mkdir(parents=True, exist_ok=True)

        for s in skills:
            dst = skills_dest / s.name
            if dst.exists() or dst.is_symlink():
                if dst.is_symlink():
                    dst.unlink()
                else:
                    shutil.rmtree(dst)
            if copy:
                shutil.copytree(s, dst)
            else:
                dst.symlink_to(s)
            created.append(str(dst))

        # Copy agents.toml and AGENTS.md
        agents_toml = self.target_dir / ".agents" / "agents.toml"
        shutil.copy2(self.kit_dir / "agents" / "agents.toml", agents_toml)
        created.append(str(agents_toml))

        agents_md = self.target_dir / "AGENTS.md"
        shutil.copy2(self.kit_dir / "rules" / "AGENTS.md", agents_md)
        created.append(str(agents_md))

        return created

    def get_capabilities(self) -> Dict[str, str]:
        return {
            "skill_discovery": "Supported (native .agents/skills/ scan)",
            "subagent_invocation": "Supported (subagent tools & live agents.toml)",
            "context_isolation": "Supported (branched/isolated workspaces)",
            "mcp_support": "Supported (native MCP server protocol)"
        }

class ClaudeCodeHostAdapter(BaseHostAdapter):
    @property
    def host_name(self) -> str:
        return "claude"

    def generate_configs(self, skills: List[Path], copy: bool = False) -> List[str]:
        created = []
        claude_skills = self.target_dir / ".claude" / "skills"
        claude_skills.mkdir(parents=True, exist_ok=True)

        for s in skills:
            dst = claude_skills / s.name
            if dst.exists() or dst.is_symlink():
                if dst.is_symlink():
                    dst.unlink()
                else:
                    shutil.rmtree(dst)
            if copy:
                shutil.copytree(s, dst)
            else:
                dst.symlink_to(s)
            created.append(str(dst))

        # Generate CLAUDE.md from AGENTS.md
        claude_md = self.target_dir / "CLAUDE.md"
        content = (self.kit_dir / "rules" / "AGENTS.md").read_text(encoding="utf-8")
        claude_md.write_text(f"# Claude Code Instructions\n\n{content}", encoding="utf-8")
        created.append(str(claude_md))

        return created

    def get_capabilities(self) -> Dict[str, str]:
        return {
            "skill_discovery": "Supported via .claude/skills/",
            "subagent_invocation": "Supported (Claude slash commands / Task runners)",
            "context_isolation": "Supported",
            "mcp_support": "Supported"
        }

class CopilotHostAdapter(BaseHostAdapter):
    @property
    def host_name(self) -> str:
        return "copilot"

    def generate_configs(self, skills: List[Path], copy: bool = False) -> List[str]:
        created = []
        agents_dir = self.target_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Copy agent profiles to .github/agents/*.agent.md
        for p in (self.kit_dir / "agents" / "profiles").glob("*.agent.md"):
            dst = agents_dir / p.name
            shutil.copy2(p, dst)
            created.append(str(dst))

        # Copilot instructions
        copilot_ins = self.target_dir / ".github" / "copilot-instructions.md"
        shutil.copy2(self.kit_dir / "rules" / "copilot-instructions.md", copilot_ins)
        created.append(str(copilot_ins))

        return created

    def get_capabilities(self) -> Dict[str, str]:
        return {
            "skill_discovery": "Conditional (.github/copilot-instructions.md references)",
            "subagent_invocation": "Supported (.github/agents/*.agent.md profiles)",
            "context_isolation": "Conditional (Chat session dependent)",
            "mcp_support": "Supported in VS Code Copilot Chat"
        }

class CursorHostAdapter(BaseHostAdapter):
    @property
    def host_name(self) -> str:
        return "cursor"

    def generate_configs(self, skills: List[Path], copy: bool = False) -> List[str]:
        created = []
        cursorrules = self.target_dir / ".cursorrules"
        tmpl = self.kit_dir / "workflows" / "templates" / "CURSORRULES-TEMPLATE.md"
        if tmpl.exists():
            shutil.copy2(tmpl, cursorrules)
            created.append(str(cursorrules))
        return created

    def get_capabilities(self) -> Dict[str, str]:
        return {
            "skill_discovery": "Instruction-guided (.cursorrules context injection)",
            "subagent_invocation": "Unsupported (single composer model session)",
            "context_isolation": "Unsupported",
            "mcp_support": "Supported"
        }

class WindsurfHostAdapter(BaseHostAdapter):
    @property
    def host_name(self) -> str:
        return "windsurf"

    def generate_configs(self, skills: List[Path], copy: bool = False) -> List[str]:
        created = []
        windsurfrules = self.target_dir / ".windsurfrules"
        tmpl = self.kit_dir / "workflows" / "templates" / "CURSORRULES-TEMPLATE.md"
        if tmpl.exists():
            shutil.copy2(tmpl, windsurfrules)
            created.append(str(windsurfrules))
        return created

    def get_capabilities(self) -> Dict[str, str]:
        return {
            "skill_discovery": "Instruction-guided (.windsurfrules)",
            "subagent_invocation": "Supported via Cascade engine",
            "context_isolation": "Conditional",
            "mcp_support": "Supported"
        }

HOST_ADAPTERS = {
    "antigravity": AntigravityHostAdapter,
    "claude": ClaudeCodeHostAdapter,
    "copilot": CopilotHostAdapter,
    "cursor": CursorHostAdapter,
    "windsurf": WindsurfHostAdapter
}

def get_adapter(host_name: str, kit_dir: Path, target_dir: Path) -> Optional[BaseHostAdapter]:
    cls = HOST_ADAPTERS.get(host_name.lower())
    return cls(kit_dir, target_dir) if cls else None
