# AI IDE & Agent Compatibility Matrix

Agents-kit is architected to support multi-stack software engineering across multiple AI Coding Agents and IDE environments.

| AI Environment / IDE | Support Level | Skill Discovery Mechanism | Subagent Invocation | Status & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Google Antigravity** | **Officially Supported** | `.agents/skills/*/SKILL.md` auto-discovered live | Via task instructions & `.agents/agents.toml` | Runtime-verified. Skills, rules, and MCP servers directly loaded into workspace. |
| **GitHub Copilot / VS Code** | **Officially Supported** | `.github/copilot-instructions.md` & `.github/agents/*.agent.md` | Via Copilot custom agent profiles | Supported. Reads instructions and agent runbooks seamlessly. |
| **Cursor** | **Officially Supported** | `.cursorrules` & `.agents/skills` | Prompt-directed | Supported. `.cursorrules` injected at root; references `.agents/skills`. |
| **Claude Code** | **Supported via Adapter** | `CLAUDE.md` / `.claude/skills/` / `.agents/` | Slash commands & subagents | Fully compatible with SKILL.md format and bash tool execution. |
| **Codex / OpenAI CLI** | **Partially Supported** | `AGENTS.md` system prompt injection | System prompt delegation | Uses standard Markdown rules and task-level skill injection. |
| **Windsurf (Codeium)** | **Supported via Adapter** | `.windsurfrules` (maps to `.cursorrules`) | Cascade workflow engine | Standard prompt and directory rule loading. |

---

## 1. Google Antigravity Integration
- **Root Files**: `.agents/skills/`, `.agents/agents.toml`, `AGENTS.md`.
- **Behavior**: Antigravity automatically indexes skills placed in `.agents/skills/` during conversation startup.
- **Progressive Disclosure**: Antigravity uses level 1 metadata from `SKILL.md` frontmatter, loading execution bodies only when invoked.

## 2. GitHub Copilot
- **Root Files**: `.github/copilot-instructions.md`, `.github/agents/*.agent.md`.
- **Behavior**: Copilot reads repository instructions automatically on each prompt.

## 3. Cursor & Windsurf
- **Root Files**: `.cursorrules`, `.windsurfrules`.
- **Behavior**: Injects high-signal steering rules and anti-slop guidelines into the agent's context window.
