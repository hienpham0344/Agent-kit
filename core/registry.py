"""
Skill Metadata Registry v2.
Supports progressive disclosure (Level 1 discovery, Level 2 selection, Level 3 execution).
Indexes rich frontmatter: triggers, aliases, dependencies, conflicts, required_tools, risk_level, version.
Provides consistency validation (missing dependencies, circular dependencies, broken paths).
"""

import os
import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

TAG_KEYWORDS: Dict[str, List[str]] = {
    "java": ["java", "jvm", "spring", "maven", "gradle", "hibernate", "jpa"],
    "python": ["python", "pydantic", "pytest", "fastapi", "django", "flask", "polars", "pandas"],
    "frontend": ["react", "nextjs", "vue", "tailwind", "css", "html", "javascript", "typescript", "ui", "ux", "browser"],
    "database": ["database", "postgres", "mysql", "sqlite", "query", "sql", "migration", "sharding"],
    "devops": ["docker", "kubernetes", "k8s", "terraform", "ci", "cd", "github actions", "helm", "aws", "gcp", "azure"],
    "security": ["security", "stride", "threat", "vulnerability", "auth", "owasp", "penetration", "secret", "sast", "jwt"],
    "testing": ["test", "tdd", "unit", "integration", "e2e", "playwright", "vitest", "fuzz"],
    "debugging": ["debug", "tracing", "perf", "valgrind", "memory leak", "profiling", "sentry", "error", "root cause"],
    "ai-llm": ["llm", "rag", "agent", "prompt", "token", "vector", "embedding", "langgraph"]
}

@dataclass
class SkillMetadata:
    name: str
    description: str
    category: str
    rel_path: str
    full_path: Path
    tags: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high
    version: str = "1.0.0"

@dataclass
class RegistryValidationReport:
    total_skills: int = 0
    valid_skills: int = 0
    missing_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    broken_paths: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class SkillRegistry:
    def __init__(self, kit_dir: Path):
        self.kit_dir = kit_dir.resolve()
        self.skills_dir = self.kit_dir / "skills"
        self._skills: Dict[str, SkillMetadata] = {}
        self._aliases_map: Dict[str, str] = {}
        self._loaded = False

    def load_catalog(self, force_reload: bool = False):
        """Level 1 Discovery: Fast catalog index scan using lightweight frontmatter parsing."""
        if self._loaded and not force_reload:
            return

        self._skills.clear()
        self._aliases_map.clear()
        if not self.skills_dir.exists():
            return

        for cat_dir in sorted(self.skills_dir.iterdir()):
            if not cat_dir.is_dir():
                continue
            cat_name = cat_dir.name
            for s_dir in sorted(cat_dir.iterdir()):
                if not s_dir.is_dir():
                    continue
                skill_md = s_dir / "SKILL.md"
                if not skill_md.exists():
                    continue

                name = s_dir.name
                desc = ""
                fm_data: Dict[str, Any] = {}

                try:
                    with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
                        first_line = f.readline()
                        if first_line.startswith("---"):
                            fm_lines = []
                            for line in f:
                                if line.startswith("---"):
                                    break
                                fm_lines.append(line)
                            fm_text = "".join(fm_lines)
                            try:
                                loaded_yaml = yaml.safe_load(fm_text)
                                if isinstance(loaded_yaml, dict):
                                    fm_data = loaded_yaml
                                    name = fm_data.get("name", name)
                                    desc = fm_data.get("description", "")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Derive tags, languages, frameworks
                searchable = f"{name} {desc} {cat_name}".lower()
                tags: Set[str] = set()
                languages: Set[str] = set()
                frameworks: Set[str] = set()

                for tag, kw_list in TAG_KEYWORDS.items():
                    for kw in kw_list:
                        if kw in searchable:
                            tags.add(tag)
                            if tag in ("java", "python"):
                                languages.add(tag)
                            if kw in ("react", "nextjs", "vue", "spring", "fastapi", "django"):
                                frameworks.add(kw)
                            break

                # Support rich frontmatter extensions
                raw_triggers = fm_data.get("triggers", [])
                triggers = [str(t).strip() for t in raw_triggers] if isinstance(raw_triggers, list) else []

                raw_aliases = fm_data.get("aliases", [])
                aliases = [str(a).strip() for a in raw_aliases] if isinstance(raw_aliases, list) else []

                raw_deps = fm_data.get("dependencies", [])
                dependencies = [str(d).strip() for d in raw_deps] if isinstance(raw_deps, list) else []

                raw_conflicts = fm_data.get("conflicts", [])
                conflicts = [str(c).strip() for c in raw_conflicts] if isinstance(raw_conflicts, list) else []

                raw_tools = fm_data.get("required_tools", [])
                required_tools = [str(t).strip() for t in raw_tools] if isinstance(raw_tools, list) else []

                risk_level = str(fm_data.get("risk_level", "low")).lower()
                version = str(fm_data.get("version", "1.0.0"))

                meta_obj = SkillMetadata(
                    name=name,
                    description=desc,
                    category=cat_name,
                    rel_path=str(skill_md.relative_to(self.kit_dir)),
                    full_path=skill_md,
                    tags=sorted(list(tags)),
                    languages=sorted(list(languages)),
                    frameworks=sorted(list(frameworks)),
                    triggers=triggers,
                    aliases=aliases,
                    dependencies=dependencies,
                    conflicts=conflicts,
                    required_tools=required_tools,
                    risk_level=risk_level,
                    version=version
                )
                self._skills[name] = meta_obj
                self._aliases_map[name.lower()] = name
                # Also map directory folder name as alias if different from frontmatter name
                folder_name = s_dir.name
                if folder_name != name:
                    self._aliases_map[folder_name.lower()] = name
                for al in aliases:
                    self._aliases_map[al.lower()] = name

        self._loaded = True

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        self.load_catalog()
        resolved_name = self._aliases_map.get(name.lower(), name)
        return self._skills.get(resolved_name)

    def list_all(self) -> List[SkillMetadata]:
        self.load_catalog()
        return list(self._skills.values())

    def get_total_count(self) -> int:
        self.load_catalog()
        return len(self._skills)

    def load_skill_content(self, name: str) -> str:
        """Level 3 Execution: Load full SKILL.md body on-demand."""
        meta = self.get_skill(name)
        if not meta or not meta.full_path.exists():
            return ""
        return meta.full_path.read_text(encoding="utf-8", errors="ignore")

    def validate_registry(self) -> RegistryValidationReport:
        """Perform comprehensive consistency checks on all indexed skills."""
        self.load_catalog()
        report = RegistryValidationReport(
            total_skills=len(self._skills),
            valid_skills=0
        )

        # 1. Path existence and dependency verification
        for name, meta in self._skills.items():
            if not meta.full_path.exists():
                report.broken_paths.append(str(meta.full_path))
                continue

            missing = [dep for dep in meta.dependencies if dep not in self._skills]
            if missing:
                report.missing_dependencies[name] = missing

            report.valid_skills += 1

        # 2. Circular dependency detection (DFS)
        visited = {}  # 0 = unvisited, 1 = visiting, 2 = visited
        cycles = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            path.append(node)
            meta = self._skills.get(node)
            if meta:
                for neighbor in meta.dependencies:
                    if neighbor not in self._skills:
                        continue
                    if visited.get(neighbor) == 1:
                        cycle_start = path.index(neighbor)
                        cycles.append(path[cycle_start:] + [neighbor])
                    elif visited.get(neighbor, 0) == 0:
                        dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        for s in self._skills:
            if visited.get(s, 0) == 0:
                dfs(s, [])

        report.circular_dependencies = cycles
        return report
