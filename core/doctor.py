"""Read-only diagnosis and safe repair of Agents-kit installations."""

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List

from core.manifest import ManifestManager, calculate_file_hash
from core.presets import CONTEXT_BUDGET_CRITICAL, CONTEXT_BUDGET_WARN
from core.registry import SkillRegistry, USING_PYYAML
from core.security import validate_skill_name

HARDCODED_PATH_RE = re.compile(r"(/home/[^/\"'\s]+|/Users/[^/\"'\s]+|[A-Za-z]:\\\\Users\\\\[^\\\\\"'\s]+)")


@dataclass
class ProjectHealth:
    status: str
    active_skills: int = 0
    broken_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    invalid_paths: List[str] = field(default_factory=list)
    extra_skills: List[str] = field(default_factory=list)
    instructions_present: bool = False
    context_budget_status: str = "OK"
    detected_hosts: List[str] = field(default_factory=list)
    host: str = "antigravity"

    @property
    def healthy(self) -> bool:
        return self.status in ("SOURCE", "MANAGED", "UNMANAGED") and not (
            self.broken_skills or self.missing_skills or self.missing_files
            or self.modified_files or self.invalid_paths
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["healthy"] = self.healthy
        return data


def _budget_status(skill_count: int) -> str:
    if skill_count >= CONTEXT_BUDGET_CRITICAL:
        return "CRITICAL"
    if skill_count >= CONTEXT_BUDGET_WARN:
        return "WARN"
    return "OK"


def inspect_project(project: Path, kit_dir: Path) -> ProjectHealth:
    """Inspect only local files; never repair or change the installation."""
    project = project.expanduser().resolve()
    if not project.is_dir():
        return ProjectHealth(status="INVALID_TARGET")

    detected_hosts: List[str] = []
    for marker, host_label in (
        ("AGENTS.md", "antigravity/codex"),
        ("CLAUDE.md", "claude"),
        (".cursorrules", "cursor"),
        (".windsurfrules", "windsurf"),
        (".github/copilot-instructions.md", "copilot"),
    ):
        if (project / marker).is_file():
            detected_hosts.append(host_label)

    if project == kit_dir.resolve():
        return ProjectHealth(
            status="SOURCE",
            instructions_present=(project / "AGENTS.md").is_file(),
            detected_hosts=detected_hosts,
        )

    manifest_manager = ManifestManager(project)
    manifest_path = manifest_manager.manifest_path
    manifest = manifest_manager.load_manifest()

    host = manifest.host if manifest else "antigravity"
    skill_roots = [project / ".agents" / "skills", project / ".claude" / "skills"]
    entries = []
    for root in skill_roots:
        if root.is_dir():
            entries.extend(root.iterdir())

    active = [entry for entry in entries if entry.is_dir() and (entry / "SKILL.md").is_file()]
    broken = sorted({
        entry.name for entry in entries
        if not (entry / "SKILL.md").is_file()
    })

    if manifest_path.exists() and manifest is None:
        status = "INVALID"
    elif manifest:
        status = "MANAGED" if manifest.installed_skills else "INCOMPLETE"
    elif entries:
        status = "UNMANAGED"
    else:
        status = "UNINSTALLED"

    active_names = {entry.name for entry in active}
    health = ProjectHealth(
        status=status,
        active_skills=len(active),
        broken_skills=broken,
        instructions_present=any((project / f).is_file() for f in ("AGENTS.md", "CLAUDE.md", ".cursorrules", ".windsurfrules")),
        context_budget_status=_budget_status(len(active)),
        detected_hosts=detected_hosts,
        host=host,
    )
    if manifest:
        for name in manifest.installed_skills:
            try:
                validate_skill_name(name)
            except ValueError:
                health.invalid_paths.append(name)
                continue
            if name not in active_names:
                health.missing_skills.append(name)
        health.missing_skills.sort()
        health.extra_skills = sorted(
            name for name in active_names if name not in manifest.installed_skills
        )
        for relative_path, expected_hash in manifest.managed_files.items():
            path = (project / relative_path).resolve()
            if not path.is_relative_to(project):
                health.invalid_paths.append(relative_path)
            elif not path.is_file():
                health.missing_files.append(relative_path)
            elif calculate_file_hash(path) != expected_hash:
                health.modified_files.append(relative_path)
    return health


def inspect_kit_environment(kit_dir: Path) -> Dict[str, Any]:
    """Inspect CLI dependencies, dynamic catalog integrity, MCP portability, and host globals."""
    kit_dir = kit_dir.resolve()
    registry = SkillRegistry(kit_dir)
    registry.load_catalog()
    validation = registry.validate_registry()

    skill_count = registry.get_total_count()
    agent_count = len(list((kit_dir / "agents" / "profiles").glob("*.agent.md")))
    recipe_count = len(list((kit_dir / "workflows" / "recipes").glob("*.md")))
    template_count = len([t for t in (kit_dir / "workflows" / "templates").iterdir() if t.is_file()])
    ref_count = len(list((kit_dir / "references").glob("**/*.md")))

    skills_json_path = kit_dir / "skills.json"
    skills_json_count = None
    if skills_json_path.is_file():
        try:
            data = json.loads(skills_json_path.read_text(encoding="utf-8"))
            skills_json_count = len(data.get("skills", []))
        except Exception:
            skills_json_count = -1

    mcp_portability_warnings: List[str] = []
    servers_file = kit_dir / "mcp" / "servers.json"
    if servers_file.is_file():
        text = servers_file.read_text(encoding="utf-8", errors="ignore")
        for match in HARDCODED_PATH_RE.findall(text):
            mcp_portability_warnings.append(f"Hardcoded machine path in mcp/servers.json: {match}")

    global_codex_rules = Path.home() / ".codex" / "AGENTS.md"
    codex_routing = global_codex_rules.is_file() and "Automatic" in global_codex_rules.read_text(
        encoding="utf-8", errors="ignore"
    )
    antigravity_plugins_dir = Path.home() / ".gemini" / "config" / "plugins"
    antigravity_plugins = sorted(p.name for p in antigravity_plugins_dir.iterdir()) if antigravity_plugins_dir.is_dir() else []

    tools_status = {
        name: shutil.which(cmd)
        for name, cmd in {
            "git": "git",
            "python3": "python3",
            "node": "node",
            "context-mode": "context-mode",
            "docker": "docker",
        }.items()
    }

    catalog_synced = skills_json_count is None or skills_json_count == skill_count
    kit_healthy = (
        sys.version_info >= (3, 11)
        and skill_count > 0
        and agent_count > 0
        and recipe_count > 0
        and template_count > 0
        and ref_count > 0
        and catalog_synced
        and not validation.missing_dependencies
        and not validation.broken_paths
        and not validation.circular_dependencies
    )

    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "pyyaml_installed": USING_PYYAML,
        "tools": tools_status,
        "catalog": {
            "skills": skill_count,
            "skills_json": skills_json_count,
            "skills_json_synced": catalog_synced,
            "agents": agent_count,
            "recipes": recipe_count,
            "templates": template_count,
            "references": ref_count,
            "missing_dependencies": validation.missing_dependencies,
            "broken_paths": validation.broken_paths,
            "circular_dependencies": validation.circular_dependencies,
        },
        "mcp_portability_warnings": mcp_portability_warnings,
        "codex_global_routing": codex_routing,
        "antigravity_plugins": antigravity_plugins,
        "kit_healthy": kit_healthy,
    }


def repair_project(project: Path, kit_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Safely repair broken skill symlinks in a managed or unmanaged project."""
    project = project.expanduser().resolve()
    kit_dir = kit_dir.resolve()
    registry = SkillRegistry(kit_dir)
    registry.load_catalog()

    repaired: List[str] = []
    unresolvable: List[str] = []

    for skills_dir in (project / ".agents" / "skills", project / ".claude" / "skills"):
        if not skills_dir.is_dir():
            continue
        for entry in sorted(skills_dir.iterdir()):
            if entry.is_symlink() and not (entry / "SKILL.md").is_file():
                meta = registry.get_skill(entry.name)
                if meta and meta.full_path.parent.is_dir():
                    repaired.append(entry.name)
                    if not dry_run:
                        entry.unlink()
                        entry.symlink_to(meta.full_path.parent)
                else:
                    unresolvable.append(entry.name)

    return {
        "dry_run": dry_run,
        "repaired_symlinks": repaired,
        "unresolvable": unresolvable,
    }
