"""
Safe Installation and Sync Planner.
Prevents destructive overwrites, detects conflicts, supports --dry-run, --backup, and --force.
Respects user-created skills and unmanaged customizations.
"""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from core.manifest import ManifestManager, calculate_file_hash
from core.presets import PRESETS
from core.security import validate_safe_destination

@dataclass
class FileOperation:
    src: Optional[Path]
    dst: Path
    action: str  # 'create', 'update', 'unchanged', 'conflict', 'skip'
    is_conflict: bool = False
    details: str = ""

@dataclass
class InstallationPlan:
    preset: str
    mode: str
    categories: List[str]
    operations: List[FileOperation] = field(default_factory=list)
    has_conflicts: bool = False

class InstallationPlanner:
    def __init__(
        self,
        kit_dir: Path,
        target_dir: Path,
        preset: str = "auto",
        copy: bool = False,
        force: bool = False,
        backup: bool = False,
        categories: Optional[List[str]] = None
    ):
        self.kit_dir = kit_dir.resolve()
        self.target_dir = target_dir.resolve()
        self.preset = preset
        self.copy = copy
        self.force = force
        self.backup = backup
        self.manifest_mgr = ManifestManager(self.target_dir)
        self.existing_manifest = self.manifest_mgr.load_manifest()

        if categories:
            self.categories = categories
        elif preset in PRESETS:
            self.categories = PRESETS[preset]
        else:
            self.categories = PRESETS.get("minimal", [])

    def plan(self) -> InstallationPlan:
        plan = InstallationPlan(
            preset=self.preset,
            mode="copy" if self.copy else "symlink",
            categories=self.categories
        )

        # 1. Plan Skill Installations
        target_skills_dir = self.target_dir / ".agents" / "skills"
        skills_dir = self.kit_dir / "skills"

        installed_skill_names = set()
        for cat in self.categories:
            cat_path = skills_dir / cat
            if not cat_path.exists():
                continue
            for s in sorted(cat_path.iterdir()):
                if s.is_dir() and (s / "SKILL.md").exists():
                    dst = target_skills_dir / s.name
                    installed_skill_names.add(s.name)
                    
                    if not dst.exists() and not dst.is_symlink():
                        plan.operations.append(FileOperation(
                            src=s, dst=dst, action="create", details="Install new skill"
                        ))
                    else:
                        # Existing destination
                        if dst.is_symlink():
                            try:
                                link_target = dst.resolve()
                                if link_target == s.resolve():
                                    plan.operations.append(FileOperation(
                                        src=s, dst=dst, action="unchanged", details="Symlink already matches"
                                    ))
                                else:
                                    plan.operations.append(FileOperation(
                                        src=s, dst=dst, action="update", details="Update symlink destination"
                                    ))
                            except Exception:
                                plan.operations.append(FileOperation(
                                    src=s, dst=dst, action="update", details="Fix broken symlink"
                                ))
                        else:
                            # dst is an actual directory
                            # Check if it was previously managed or if it's a custom user skill
                            is_managed = (self.existing_manifest and s.name in self.existing_manifest.installed_skills)
                            if is_managed or self.force:
                                plan.operations.append(FileOperation(
                                    src=s, dst=dst, action="update", details="Update managed skill copy"
                                ))
                            else:
                                plan.operations.append(FileOperation(
                                    src=s, dst=dst, action="conflict", is_conflict=True,
                                    details=f"Unmanaged skill directory exists: {dst}. Use --force to overwrite."
                                ))
                                plan.has_conflicts = True

        # 2. Plan Core Configuration Files
        configs = [
            (self.kit_dir / "agents" / "agents.toml", self.target_dir / ".agents" / "agents.toml"),
            (self.kit_dir / "rules" / "AGENTS.md", self.target_dir / "AGENTS.md"),
            (self.kit_dir / "rules" / "copilot-instructions.md", self.target_dir / ".github" / "copilot-instructions.md"),
        ]

        cursor_tmpl = self.kit_dir / "workflows" / "templates" / "CURSORRULES-TEMPLATE.md"
        if cursor_tmpl.exists():
            configs.append((cursor_tmpl, self.target_dir / ".cursorrules"))

        hook_src = self.kit_dir / "workflows" / "hooks" / "context-mode.json"
        if hook_src.exists():
            configs.append((hook_src, self.target_dir / ".github" / "hooks" / "context-mode.json"))

        for src, dst in configs:
            if not dst.exists():
                plan.operations.append(FileOperation(
                    src=src, dst=dst, action="create", details="Create configuration file"
                ))
            else:
                current_hash = calculate_file_hash(dst)
                src_hash = calculate_file_hash(src)
                if current_hash == src_hash:
                    plan.operations.append(FileOperation(
                        src=src, dst=dst, action="unchanged", details="Identical configuration file"
                    ))
                else:
                    rel = str(dst.relative_to(self.target_dir))
                    was_managed = (self.existing_manifest and rel in self.existing_manifest.managed_files)
                    
                    if was_managed and self.existing_manifest.managed_files[rel] == current_hash:
                        # File was unmodified by user since last install
                        plan.operations.append(FileOperation(
                            src=src, dst=dst, action="update", details="Clean update of unedited configuration"
                        ))
                    elif self.force:
                        plan.operations.append(FileOperation(
                            src=src, dst=dst, action="update", details="Force update configuration file"
                        ))
                    else:
                        plan.operations.append(FileOperation(
                            src=src, dst=dst, action="conflict", is_conflict=True,
                            details=f"User modified config detected at {rel}. Use --force or --backup to update."
                        ))
                        plan.has_conflicts = True

        return plan

    def execute(self, plan: InstallationPlan, dry_run: bool = False) -> Dict[str, Any]:
        results = {"created": 0, "updated": 0, "unchanged": 0, "conflicts": 0, "backed_up": 0}

        if dry_run:
            for op in plan.operations:
                if op.action == "create":
                    results["created"] += 1
                elif op.action == "update":
                    results["updated"] += 1
                elif op.action == "unchanged":
                    results["unchanged"] += 1
                elif op.is_conflict:
                    results["conflicts"] += 1
            return results

        if plan.has_conflicts and not self.force:
            raise RuntimeError("Installation aborted due to file conflicts. Use --force or inspect conflicts.")

        backup_dir = self.target_dir / ".agents" / "backups"
        if self.backup:
            backup_dir.mkdir(parents=True, exist_ok=True)

        managed_files = {}
        installed_skills = []

        for op in plan.operations:
            if op.action == "unchanged":
                results["unchanged"] += 1
                if op.dst.is_file():
                    rel = str(op.dst.relative_to(self.target_dir))
                    managed_files[rel] = calculate_file_hash(op.dst)
                continue

            if op.is_conflict and not self.force:
                results["conflicts"] += 1
                continue

            op.dst.parent.mkdir(parents=True, exist_ok=True)

            # Backup if requested
            if self.backup and op.dst.exists():
                b_path = backup_dir / (op.dst.name + ".bak")
                if op.dst.is_file():
                    shutil.copy2(op.dst, b_path)
                elif op.dst.is_dir() and not op.dst.is_symlink():
                    shutil.copytree(op.dst, b_path, dirs_exist_ok=True)
                results["backed_up"] += 1

            # Perform write
            if op.dst.is_symlink() or op.dst.is_file():
                op.dst.unlink(missing_ok=True)
            elif op.dst.is_dir():
                shutil.rmtree(op.dst)

            if op.src:
                if op.dst.parent.name == "skills":
                    installed_skills.append(op.dst.name)
                    if self.copy:
                        shutil.copytree(op.src, op.dst)
                    else:
                        op.dst.symlink_to(op.src)
                else:
                    shutil.copy2(op.src, op.dst)
                    rel = str(op.dst.relative_to(self.target_dir))
                    managed_files[rel] = calculate_file_hash(op.dst)

            if op.action == "create":
                results["created"] += 1
            else:
                results["updated"] += 1

        # Also copy agent profiles, workflows, templates, references
        self._copy_auxiliary_assets()

        # Save manifest
        self.manifest_mgr.save_manifest(
            preset=self.preset,
            mode=plan.mode,
            categories=self.categories,
            installed_skills=installed_skills,
            managed_files=managed_files
        )

        return results

    def _copy_auxiliary_assets(self):
        """Install agent profiles, runbooks, templates, and reference guides."""
        github_agents_dir = self.target_dir / ".github" / "agents"
        docs_wf_dir = self.target_dir / "docs" / "workflows"
        docs_tmpl_dir = self.target_dir / "docs" / "templates"
        docs_ref_dir = self.target_dir / "docs" / "references"

        github_agents_dir.mkdir(parents=True, exist_ok=True)
        docs_wf_dir.mkdir(parents=True, exist_ok=True)
        docs_tmpl_dir.mkdir(parents=True, exist_ok=True)
        docs_ref_dir.mkdir(parents=True, exist_ok=True)

        for p in (self.kit_dir / "agents" / "profiles").glob("*.agent.md"):
            shutil.copy2(p, github_agents_dir / p.name)

        for r in (self.kit_dir / "workflows" / "recipes").glob("*.md"):
            shutil.copy2(r, docs_wf_dir / r.name)

        for t in (self.kit_dir / "workflows" / "templates").iterdir():
            if t.is_file():
                shutil.copy2(t, docs_tmpl_dir / t.name)

        for rf in (self.kit_dir / "references").glob("**/*.md"):
            rel = rf.relative_to(self.kit_dir / "references")
            dst = docs_ref_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(rf, dst)
