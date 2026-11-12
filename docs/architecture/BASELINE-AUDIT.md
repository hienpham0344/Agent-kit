# Agents-kit Baseline Audit & Discovery Report (vNext)

**Date**: 2026-10-23  
**Status**: Completed Baseline Assessment  
**Auditor**: Antigravity Principal Software Engineer & AI Architect  

---

## 1. Executive Summary & Inventory Baseline

| Artifact / Component | Actual Count | Documented / Expected | Baseline Status | Notes / Discrepancies |
| :--- | :--- | :--- | :--- | :--- |
| **Curated Skill Directories** (`skills/*/*`) | **285** | 285 | ✅ Intact | 21 domains / categories |
| **Valid YAML Frontmatter** | **284 / 285** | 285 | ⚠️ 1 Syntax Error | `planning-grilling/gstack-product-launch-workflow/SKILL.md` unquoted colon |
| **Agent Profiles** (`agents/profiles/*.agent.md`) | **22** | 22 | ✅ Intact | Frontmatter valid |
| **Standard Workflows** (`workflows/recipes/*.md`) | **10** | 10 | ✅ Intact | Structured markdown files |
| **Templates** (`workflows/templates/*`) | **18** | 18 | ✅ Intact | All 18 expected files exist |
| **Reference Guides** (`references/**/*.md`) | **6** | 6 | ✅ Intact | All 6 cheat sheets present |
| **Active Rules** (`rules/*`, `AGENTS.md`) | **3** | 3 | ✅ Intact | `AGENTS.md`, `copilot-instructions.md`, `agents.toml` |
| **MCP Servers** (`mcp/servers.json`) | **10** | 10 | ⚠️ Verification Gap | Only checks `shutil.which(cmd)`; no client config / health check |
| **Installed in `.agents/skills`** | **277** | 285 | ⚠️ Incomplete | Root `.agents/skills/` has 277 symlinks (8 missing from root dev env) |
| **Current Test Suite** (`tests/test_kit.py`) | **8 tests** | N/A | ⚠️ Superficial | Only tests file existence & counts; zero behavioral tests |

---

## 2. Categorized Findings & Vulnerability Matrix

### P0 — Critical Security, Data Loss & Core Detection Bugs

#### [P0-1] Hardcoded `detect_project_stack` Always Returns `"full"`
- **File**: `bin/agents-kit:78-98`
- **Evidence**:
  ```python
  def detect_project_stack(target_path: Path) -> str:
      ...
      if detected:
          print(f"🔎 Auto-detected stack: {', '.join(detected)}")
      return "full"  # ALWAYS returns full!
  ```
- **Impact**: Any user running `agents-kit install . --preset auto` or `agents-kit install .` in an empty or specialized project gets all 285 skills regardless of whether it's Python, Java, or an empty directory.
- **Remediation**: Implement structured project detection returning languages, frameworks, infrastructure, evidence, confidence, and recommended categories / presets. Default to `minimal` on empty/uncertain projects.

#### [P0-2] Destructive Overwrites & Custom Skill Deletion on `install`
- **File**: `bin/agents-kit:179-195`
- **Evidence**:
  ```python
  dst = target_skills_dir / s.name
  if dst.exists() or dst.is_symlink():
      if dst.is_symlink() or dst.is_file():
          dst.unlink()
      else:
          shutil.rmtree(dst)  # DESTRUCTIVE: deletes user's custom directory if name collides!
  ```
  `AGENTS.md`, `.github/copilot-instructions.md`, and `.agents/agents.toml` are overwritten directly with `shutil.copy2` with zero backup and zero conflict checking.
- **Impact**: Silent data loss of user customizations, custom skills, and tailored agent configurations.
- **Remediation**: Build an `InstallationPlanner` with transaction manifest, `--dry-run`, `--backup`, `--force`, conflict policies, and managed file tracking.

#### [P0-3] Path Traversal, Symlink Escape & Unsafe Deletion in `agents-kit add`
- **File**: `bin/agents-kit:438-532`
- **Evidence**:
  - `skill_name` extracted from frontmatter or folder name can contain `..` or absolute paths (`/etc/...`), escaping target project bounds.
  - Remote repository `git clone` is not pinned to commit/tag.
  - Overwrites existing destination folder via `shutil.rmtree(target_folder)` without warning.
- **Impact**: Arbitrary file overwrite / deletion if malicious skill name is supplied.
- **Remediation**: Validate skill names (`^[a-z0-9-]+$`), ensure destination resolved path is strictly within target directory (`relative_to` check), implement dry-run and provenance tracking.

#### [P0-4] Broken/Forced `sync` Reverts User Settings to `full` & Symlink
- **File**: `bin/agents-kit:230-235`
- **Evidence**:
  ```python
  def cmd_sync(args):
      args.preset = "full"
      args.copy = False
      cmd_install(args)
  ```
- **Impact**: Running `agents-kit sync` on a project that deliberately installed `--preset backend --copy` completely destroys the installation choice, forces all 285 skills, and replaces copies with symlinks.
- **Remediation**: Record an `agents-kit.manifest.json` in target storing preset, categories, install mode (copy/symlink), version, and managed file hashes. `sync` respects the recorded manifest.

#### [P0-5] Subprocess Calls in CLI Swallow Exit Codes & Mislead Diagnostics
- **File**: `bin/agents-kit:360-372`
- **Evidence**:
  ```python
  def cmd_test(args):
      subprocess.run([sys.executable, str(KIT_DIR / "tests" / "test_kit.py")])
      # Returncode not checked! Always exits with 0 even if test failed!
  ```
- **Impact**: CI/CD pipelines relying on `agents-kit test` will always pass (exit code 0) even when tests completely fail.
- **Remediation**: Check `res.returncode` and propagate via `sys.exit(res.returncode)`.

---

### P1 — Core Functionality, Presets, Skill Discovery & MCP Health

#### [P1-1] Broken Presets in Code vs README
- **Files**: `bin/agents-kit:20-76` vs `README.md:151-160`
- **Evidence**:
  - `devops` preset in `bin/agents-kit` has: `["ops-guardrails", "security-threat", "engineering-core"]`. It is completely missing `cloud-infra`, `sre-observability`, and `cloud-aws-gcp-azure` (which are documented in the README).
  - `security` preset in `bin/agents-kit` is missing `security-redteam`.
- **Impact**: Users installing `--preset devops` get zero cloud or SRE skills despite what the README claims.
- **Remediation**: Align `PRESETS` with actual categories and documentation.

#### [P1-2] Syntax Error in `gstack-product-launch-workflow/SKILL.md`
- **File**: `skills/planning-grilling/gstack-product-launch-workflow/SKILL.md:3`
- **Evidence**:
  `description: Garry Tan / YC product engineering workflow: Think, Design...` contains an unquoted colon, causing PyYAML `yaml.scanner.ScannerError`.
- **Impact**: Automated parsers, export-skills-json, or YAML linters fail.
- **Remediation**: Wrap description in quotes.

#### [P1-3] Lack of Intelligent Skill Recommendation
- **Current State**: Only substring keyword matching across 285 skills (`cmd_search`). No task analysis, no stack weighting, no explanation of why a skill is chosen, no progressive disclosure.
- **Remediation**: Build deterministic, high-precision recommendation engine (`agents-kit recommend "<task>"` and `--explain`) evaluating task intent, stack tokens, tags, and category weights.

#### [P1-4] MCP Health Verification Is Superficial
- **File**: `tools/mcp_manager.py`
- **Evidence**:
  Only checks `shutil.which(cmd_bin)`. If `npx` exists on system, it claims all 7 npx-based MCP servers (filesystem, postgres, sqlite, etc.) are "AVAILABLE", even if node modules are uninstalled, database credentials fail, or network is down.
- **Remediation**: Distinguish 4 levels: 1) Declared in catalog, 2) Binary available in PATH, 3) Config valid, 4) Protocol handshake / ping verified. Add `agents-kit mcp doctor`.

---

### P2 — Maintainability, Modularity & Architecture

#### [P2-1] Monolithic CLI Script (`bin/agents-kit`)
- **File**: `bin/agents-kit` (~625 lines)
- **Problem**: Holds CLI parsing, stack detection, installation logic, sync, audit, doctor, search, export, and git importing in a single script with minimal modularity.
- **Remediation**: Refactor into modular package under `core/` (`detection.py`, `registry.py`, `planner.py`, `manifest.py`, `routing.py`, `validator.py`, `security.py`) while preserving `bin/agents-kit` as a clean, backward-compatible entry point.

#### [P2-2] Token Savings Claim ("up to 98%") Unmeasured
- **Evidence**: Claimed in README without reproducible baseline benchmark script.
- **Remediation**: Build `tools/token_benchmark.py` providing quantifiable token usage comparisons (Full prompt loading vs Level 1/2 metadata routing vs Context Mode sandbox).

---

## 3. Next Action Plan (Execution Stages)

1. **Stage A**: Fix YAML syntax error in `gstack-product-launch-workflow/SKILL.md`.
2. **Stage B**: Write failing reproduction tests for project detection, presets, destructive installation, exit codes, and path traversal.
3. **Stage C**: Implement modular `core/` architecture with safety guards, safe installation planner, manifest manager, and refined stack detection.
4. **Stage D**: Implement intelligent skill recommendation engine & progressive loading metadata registry.
5. **Stage E**: Upgrade MCP manager with 4-level verification and doctor diagnostics.
6. **Stage F**: Run benchmarks, update test suite to 100% pass, and align documentation.
