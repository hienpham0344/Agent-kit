"""
Skill Metadata Registry and Progressive Loading Engine.
Implements 3-Level Progressive Disclosure:
  Level 1 (Discovery): Fast metadata indexing (name, description, category, tags) without full file loading.
  Level 2 (Selection): Detailed attributes, triggers, related workflows, and target frameworks.
  Level 3 (Execution): Full SKILL.md body and auxiliary files loaded on-demand.
"""

import os
import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

TAG_KEYWORDS: Dict[str, List[str]] = {
    "java": ["java", "jvm", "spring", "maven", "gradle", "hibernate", "jpa"],
    "python": ["python", "pydantic", "pytest", "fastapi", "django", "flask", "polars", "pandas"],
    "frontend": ["react", "nextjs", "vue", "tailwind", "css", "html", "javascript", "typescript", "ui", "ux", "browser"],
    "database": ["database", "postgres", "mysql", "sqlite", "query", "sql", "migration", "sharding"],
    "devops": ["docker", "kubernetes", "k8s", "terraform", "ci", "cd", "github actions", "helm", "aws", "gcp", "azure"],
    "security": ["security", "stride", "threat", "vulnerability", "auth", "owasp", "penetration", "secret", "sast"],
    "testing": ["test", "tdd", "unit", "integration", "e2e", "playwright", "vitest", "fuzz"],
    "debugging": ["debug", "tracing", "perf", "valgrind", "memory leak", "profiling", "sentry"],
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

class SkillRegistry:
    def __init__(self, kit_dir: Path):
        self.kit_dir = kit_dir.resolve()
        self.skills_dir = self.kit_dir / "skills"
        self._skills: Dict[str, SkillMetadata] = {}
        self._loaded = False

    def load_catalog(self, force_reload: bool = False):
        """Level 1 Discovery: Fast catalog index scan using lightweight frontmatter parsing."""
        if self._loaded and not force_reload:
            return

        self._skills.clear()
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
                content = ""
                try:
                    with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
                        # Read frontmatter safely
                        first_line = f.readline()
                        if first_line.startswith("---"):
                            fm_lines = []
                            for line in f:
                                if line.startswith("---"):
                                    break
                                fm_lines.append(line)
                            fm_text = "".join(fm_lines)
                            try:
                                meta = yaml.safe_load(fm_text)
                                if isinstance(meta, dict):
                                    name = meta.get("name", name)
                                    desc = meta.get("description", "")
                            except Exception:
                                pass
                except Exception:
                    pass

                # Derive tags, languages, triggers heuristically
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

                meta_obj = SkillMetadata(
                    name=name,
                    description=desc,
                    category=cat_name,
                    rel_path=str(skill_md.relative_to(self.kit_dir)),
                    full_path=skill_md,
                    tags=sorted(list(tags)),
                    languages=sorted(list(languages)),
                    frameworks=sorted(list(frameworks))
                )
                self._skills[name] = meta_obj

        self._loaded = True

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        self.load_catalog()
        return self._skills.get(name)

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
