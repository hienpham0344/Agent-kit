"""
Deterministic Skill Recommendation and Routing Engine v2.
Integrates multilingual intent recognition (Vietnamese & English), project stack context,
rich frontmatter triggers, dependency/conflict resolution, and explainable decision categories.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any

from core.registry import SkillRegistry, SkillMetadata
from core.detection import StackDetectionResult, detect_project_stack
from core.intent import extract_intents, IntentExtractionResult

DECISION_AUTO_SELECT = "auto_select"
DECISION_RECOMMEND = "recommend"
DECISION_CLARIFICATION = "clarification_required"
DECISION_NO_MATCH = "no_match"

@dataclass
class SkillRecommendation:
    skill: SkillMetadata
    score: float
    reasons: List[str] = field(default_factory=list)
    resolved_dependencies: List[str] = field(default_factory=list)
    has_conflicts: bool = False

@dataclass
class RecommendationResult:
    task: str
    intent_analysis: IntentExtractionResult
    project_context: Optional[StackDetectionResult]
    decision: str
    selected_skills: List[SkillMetadata] = field(default_factory=list)
    recommendations: List[SkillRecommendation] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "decision": self.decision,
            "primary_intent": self.intent_analysis.primary_intent,
            "secondary_intents": self.intent_analysis.secondary_intents,
            "detected_technologies": self.intent_analysis.detected_technologies,
            "project_stack": self.project_context.detected_languages if self.project_context else [],
            "recommendations": [
                {
                    "name": r.skill.name,
                    "category": r.skill.category,
                    "score": round(r.score, 2),
                    "reasons": r.reasons,
                    "dependencies": r.resolved_dependencies,
                    "risk_level": r.skill.risk_level
                }
                for r in self.recommendations
            ],
            "conflicts": self.conflicts,
            "warnings": self.warnings
        }

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
        intent_res = extract_intents(task)
        task_lower = task.lower()
        # 0. Check for casual chatter / negative queries / trivial queries
        chatter_markers = ["hello", "xin chao", "joke", "weather", "essay", "just testing", "thoi tiet"]
        trivial_markers = ["typo", "chinh ta", "rename variable", "doi ten bien", "copyright", "comment"]

        is_chatter = any(m in task_lower for m in chatter_markers)
        is_trivial = any(m in task_lower for m in trivial_markers)

        if is_chatter:
            return RecommendationResult(
                task=task,
                intent_analysis=intent_res,
                project_context=stack_ctx,
                decision=DECISION_NO_MATCH,
                selected_skills=[],
                recommendations=[],
                conflicts=[],
                warnings=["Query appears to be general conversation or non-technical. No skills activated."]
            )

        if is_trivial:
            return RecommendationResult(
                task=task,
                intent_analysis=intent_res,
                project_context=stack_ctx,
                decision=DECISION_NO_MATCH,
                selected_skills=[],
                recommendations=[],
                conflicts=[],
                warnings=["Trivial / localized edit. Executed directly without loading specialized skills."]
            )

        task_words = intent_res.tokens
        scored: List[Tuple[float, SkillMetadata, List[str]]] = []

        all_intents = [intent_res.primary_intent] + intent_res.secondary_intents

        for skill in self.registry.list_all():
            score = 0.0
            reasons = []

            # 1. Exact Name / Aliases Matching
            skill_name_clean = skill.name.lower().replace("-", " ")
            skill_tokens = set(re.findall(r"\b[a-zA-Z0-9_]{2,}\b", skill_name_clean))

            name_overlap = task_words.intersection(skill_tokens)
            if name_overlap:
                score += len(name_overlap) * 5.0
                reasons.append(f"Name matched: {', '.join(name_overlap)}")

            for al in skill.aliases:
                if al.lower() in intent_res.normalized_text:
                    score += 6.0
                    reasons.append(f"Alias matched: {al}")

            # 2. Rich Frontmatter Triggers Matching
            for tr in skill.triggers:
                if tr.lower() in intent_res.normalized_text or tr.lower() in task.lower():
                    score += 7.0
                    reasons.append(f"Trigger matched: '{tr}'")

            # 3. Multilingual Intent Matching
            if "debugging" in all_intents:
                if skill.name in ("systematic-debugging", "debugging-strategies", "memory-leak-detection"):
                    weight = 8.0 if intent_res.primary_intent == "debugging" else 4.0
                    score += weight
                    reasons.append("Task requests debugging/troubleshooting")
                elif "sre" in skill.category or "observability" in skill.category:
                    score += 3.0

            if "testing" in all_intents:
                if "testing" in skill.category or "test" in skill.name:
                    weight = 6.0 if intent_res.primary_intent == "testing" else 3.0
                    score += weight
                    reasons.append("Task requests testing/verification")

            if "security" in all_intents:
                if "security" in skill.category or any(k in skill.name for k in ("auth", "jwt", "owasp", "vault")):
                    weight = 7.0 if intent_res.primary_intent == "security" else 4.0
                    score += weight
                    reasons.append("Task requests authentication / security")

            # 4. Detected Technologies from Multilingual Engine
            for tech in intent_res.detected_technologies:
                if tech in skill.tags or tech in skill.languages or tech in skill.frameworks or tech in skill.name:
                    score += 5.0
                    reasons.append(f"Technology match ({tech})")

            # 5. Project Stack Context Alignment
            if stack_ctx:
                for lang in stack_ctx.detected_languages:
                    if lang in skill.languages or lang in skill.tags:
                        score += 3.5
                        reasons.append(f"Aligned with project language ({lang})")
                for fw in stack_ctx.frameworks:
                    if fw in skill.frameworks or fw in skill.tags:
                        score += 4.5
                        reasons.append(f"Aligned with project framework ({fw})")

            # 6. Description Substring Overlap
            desc_words = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", skill.description.lower()))
            desc_overlap = task_words.intersection(desc_words)
            if desc_overlap:
                score += len(desc_overlap) * 1.5
                reasons.append(f"Description matches: {', '.join(list(desc_overlap)[:3])}")

            if score >= min_score:
                scored.append((score, skill, reasons))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        top_candidates = scored[:top_k]

        # Resolve dependencies & detect conflicts
        recommendations: List[SkillRecommendation] = []
        conflicts: List[str] = []
        warnings: List[str] = []

        top_skill_names = {item[1].name for item in top_candidates}

        for score, skill, reasons in top_candidates:
            # Resolve dependencies
            resolved_deps = []
            for dep in skill.dependencies:
                dep_meta = self.registry.get_skill(dep)
                if dep_meta:
                    resolved_deps.append(dep)
                else:
                    warnings.append(f"Skill '{skill.name}' declares missing dependency '{dep}'")

            # Check conflicts
            has_conflict = False
            for conf in skill.conflicts:
                if conf in top_skill_names:
                    has_conflict = True
                    conflicts.append(f"Conflict detected between '{skill.name}' and '{conf}'")

            recommendations.append(SkillRecommendation(
                skill=skill,
                score=score,
                reasons=reasons,
                resolved_dependencies=resolved_deps,
                has_conflicts=has_conflict
            ))

        # Determine decision policy
        if not recommendations:
            decision = DECISION_NO_MATCH
        elif recommendations[0].score >= 12.0:
            decision = DECISION_AUTO_SELECT
        elif recommendations[0].score >= 5.0:
            decision = DECISION_RECOMMEND
        else:
            decision = DECISION_CLARIFICATION

        selected = [r.skill for r in recommendations if r.score >= 8.0][:2]

        return RecommendationResult(
            task=task,
            intent_analysis=intent_res,
            project_context=stack_ctx,
            decision=decision,
            selected_skills=selected,
            recommendations=recommendations,
            conflicts=conflicts,
            warnings=warnings
        )
