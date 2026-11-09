"""Read-only diagnosis of an Agents-kit project installation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from core.manifest import ManifestManager, calculate_file_hash
from core.security import validate_skill_name


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

    @property
    def healthy(self) -> bool:
        return self.status in ("SOURCE", "MANAGED", "UNMANAGED") and not (
            self.broken_skills or self.missing_skills or self.missing_files
            or self.modified_files or self.invalid_paths
        )


def inspect_project(project: Path, kit_dir: Path) -> ProjectHealth:
    """Inspect only local files; never repair or change the installation."""
    project = project.expanduser().resolve()
    if not project.is_dir():
        return ProjectHealth(status="INVALID_TARGET")
    if project == kit_dir.resolve():
        return ProjectHealth(status="SOURCE", instructions_present=(project / "AGENTS.md").is_file())

    manifest_manager = ManifestManager(project)
    manifest_path = manifest_manager.manifest_path
    manifest = manifest_manager.load_manifest()
    skills_dir = project / ".agents" / "skills"
    entries = list(skills_dir.iterdir()) if skills_dir.is_dir() else []
    active = [entry for entry in entries if entry.is_dir() and (entry / "SKILL.md").is_file()]
    broken = sorted(
        entry.name for entry in entries
        if not (entry / "SKILL.md").is_file()
    )

    if manifest_path.exists() and manifest is None:
        status = "INVALID"
    elif manifest:
        status = "MANAGED" if manifest.installed_skills else "INCOMPLETE"
    elif entries:
        status = "UNMANAGED"
    else:
        status = "UNINSTALLED"

    health = ProjectHealth(
        status=status,
        active_skills=len(active),
        broken_skills=broken,
        instructions_present=(project / "AGENTS.md").is_file(),
    )
    if manifest:
        for name in manifest.installed_skills:
            try:
                validate_skill_name(name)
            except ValueError:
                health.invalid_paths.append(name)
                continue
            if not (skills_dir / name / "SKILL.md").is_file():
                health.missing_skills.append(name)
        health.missing_skills.sort()
        health.extra_skills = sorted(
            entry.name for entry in active if entry.name not in manifest.installed_skills
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
