"""
Deterministic Skill Recommendation and Routing Engine.
Matches user task description and project context to relevant skills without loading all files.
Produces ranked recommendations with detailed rationale, confidence scores, and conflict warnings.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set

from core.registry import SkillRegistry, SkillMetadata
from core.detection import StackDetectionResult, detect_project_stack

@dataclass
class SkillRecommendation:
    skill: SkillMetadata
    score: float
    reasons: List[str] = field(default_factory=list)

@dataclass
class RecommendationResult:
    task: str
    project_context: Optional[StackDetectionResult]
    recommendations: List[SkillRecommendation] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

class SkillRouter:
    def __init__(self, kit_dir: Path):
        self.kit_dir = kit_dir.resolve()
        self.registry = SkillRegistry(self.kit_dir)
        self.registry.load_catalog()

    def recommend(
        self,
        task: str,
        target_dir: Optional[Path] = None,
        top_k: int = 5,
        min_score: float = 2.0
    ) -> RecommendationResult:
        stack_ctx = detect_project_stack(target_dir) if target_dir else None
        task_clean = task.lower()
        task_words = set(re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", task_clean))

        scored: List[Tuple[float, SkillMetadata, List[str]]] = []

        for skill in self.registry.list_all():
            score = 0.0
            reasons = []

            # 1. Exact Name Matching or Sub-token Matching
            skill_name_clean = skill.name.lower().replace("-", " ")
            skill_tokens = set(re.findall(r"\b[a-zA-Z0-9_]{2,}\b", skill_name_clean))

            overlap = task_words.intersection(skill_tokens)
            if overlap:
                score += len(overlap) * 5.0
                reasons.append(f"Name tokens matched: {', '.join(overlap)}")

            # 2. Key Action Matching
            is_debugging = any(w in task_words for w in ("debug", "error", "failing", "failure", "crash", "bug", "trace", "slow"))
            if is_debugging and skill.name in ("systematic-debugging", "debugging-strategies", "memory-leak-detection"):
                score += 8.0
                reasons.append("Task requests debugging/troubleshooting")

            is_testing = any(w in task_words for w in ("test", "testing", "unit", "tdd", "mock", "regression"))
            if is_testing and "testing" in skill.category:
                score += 5.0
                reasons.append("Task requests testing/verification")

            is_security = any(w in task_words for w in ("auth", "security", "threat", "vulnerability", "token", "jwt", "login", "csrf"))
            if is_security and "security" in skill.category:
                score += 6.0
                reasons.append("Task requests authentication / security enforcement")

            # 3. Stack Context Alignment
            if stack_ctx:
                for lang in stack_ctx.detected_languages:
                    if lang in skill.languages or lang in skill.tags:
                        score += 4.0
                        reasons.append(f"Aligned with detected language ({lang})")
                for fw in stack_ctx.frameworks:
                    if fw in skill.frameworks or fw in skill.tags:
                        score += 5.0
                        reasons.append(f"Aligned with detected framework ({fw})")

            # 4. Description Content Overlap
            desc_words = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", skill.description.lower()))
            desc_overlap = task_words.intersection(desc_words)
            if desc_overlap:
                score += len(desc_overlap) * 1.5
                reasons.append(f"Description matches: {', '.join(list(desc_overlap)[:3])}")

            if score >= min_score:
                scored.append((score, skill, reasons))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        # Check for potential duplicates / conflicting advice
        conflicts = []
        top_items = scored[:top_k]
        top_names = {s[1].name for s in top_items}
        if "test-driven-development" in top_names and "systematic-debugging" in top_names:
            conflicts.append("Note: For bugs, run 'systematic-debugging' first to isolate root cause before applying TDD reproduction.")

        recommendations = [
            SkillRecommendation(skill=item[1], score=item[0], reasons=item[2])
            for item in top_items
        ]

        return RecommendationResult(
            task=task,
            project_context=stack_ctx,
            recommendations=recommendations,
            conflicts=conflicts
        )
