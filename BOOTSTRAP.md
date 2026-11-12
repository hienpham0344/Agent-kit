# AI Agent Bootstrap Guide (`Agents-kit`)

Follow these exact steps when a user provides this repository (`https://github.com/hienpham0344/Agent-kit`) and asks you to set up a target project.

## 1. Locate or Clone the Kit (Once per Machine)

```bash
if command -v agents-kit >/dev/null 2>&1; then
  AGENTS_KIT_BIN="$(command -v agents-kit)"
elif [ -x "$HOME/.agents-kit/bin/agents-kit" ]; then
  AGENTS_KIT_BIN="$HOME/.agents-kit/bin/agents-kit"
else
  git clone --depth 1 https://github.com/hienpham0344/Agent-kit.git "$HOME/.agents-kit"
  AGENTS_KIT_BIN="$HOME/.agents-kit/bin/agents-kit"
fi
```

Optional global CLI registration (Python 3.11+ stdlib only, no `pip` required):

```bash
"$AGENTS_KIT_BIN" setup-env --symlink-bin
```

## 2. Verify Kit & Environment Health

```bash
"$AGENTS_KIT_BIN" doctor --json
```

Confirm `"kit_healthy": true` before installing into any project.

## 3. Preview & Install Into the Target Project

Detect your host (`antigravity`, `claude`, `codex`, `cursor`, `copilot`, `windsurf`, or `all`) and run `--dry-run` first:

```bash
"$AGENTS_KIT_BIN" install /path/to/target-project --preset auto --host antigravity --backup --dry-run
"$AGENTS_KIT_BIN" install /path/to/target-project --preset auto --host antigravity --backup
```

- Use `--copy` instead of symlinks if the target team commits `.agents/` to Git or shares across machines.
- Avoid `--preset full` unless explicitly requested; default `--preset auto` keeps active skills under the AI host context budget.

## 4. Verify Target Project Health

```bash
"$AGENTS_KIT_BIN" doctor --project /path/to/target-project --json
```

Expected: `"status": "MANAGED"`, `"healthy": true`, `"broken_skills": []`.

## 5. Host Activation Notes

- **Google Antigravity:** Reads `.agents/skills/` and `AGENTS.md` automatically. Roles in `.agents/agents.toml` are blueprints; spawn them in-session via `define_subagent` + `invoke_subagent`.
- **Claude Code:** Use `--host claude` (creates `.claude/skills/` and `CLAUDE.md`).
- **Codex:** Use `--host codex` (creates `.agents/skills/` and `AGENTS.md`).
- **Cursor / Windsurf:** Use `--host cursor` or `--host windsurf`.
- **GitHub Copilot:** Use `--host copilot` (creates `.github/copilot-instructions.md` and `.github/agents/*.agent.md`).

## 6. Clean Repair or Uninstall

```bash
"$AGENTS_KIT_BIN" doctor --project /path/to/target-project --fix
"$AGENTS_KIT_BIN" uninstall /path/to/target-project --dry-run
```
