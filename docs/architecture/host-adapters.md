# Native AI Host Adapters & Capability Matrix

Agents-Kit provides native configuration generation for top AI coding environments.

| Host Environment | Configuration Location | Skill Discovery | Agent Invocation | Context Isolation | MCP Protocol |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Antigravity** | `.agents/skills/`, `.agents/agents.toml`, `AGENTS.md` | Native (Automatic scan) | Supported (`invoke_subagent` & `.agents/agents.toml`) | Supported (Branch / Worktree) | Native |
| **Claude Code** | `.claude/skills/`, `CLAUDE.md` | Native (`.claude/skills/`) | Supported (Slash commands / Task runners) | Supported | Native |
| **GitHub Copilot / VS Code** | `.github/agents/*.agent.md`, `.github/copilot-instructions.md` | Conditional (Instruction-guided) | Supported (`.github/agents/` profiles) | Conditional | Native (VS Code MCP) |
| **Cursor** | `.cursorrules` | Instruction-guided | Unsupported (Single session composer) | Unsupported | Native |
| **Windsurf** | `.windsurfrules` | Instruction-guided | Supported (Cascade engine) | Conditional | Native |

---

## Installation via CLI
```bash
# Target specific host
agents-kit install . --host claude --preset auto
agents-kit install . --host copilot --preset backend
agents-kit install . --host all --preset full --dry-run
```
