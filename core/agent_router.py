"""
Agent Registry and Intelligent Agent Router.
Loads and models all 22 configured subagents from agents.toml and profiles.
Implements capability matching, skill readiness checks, and conservative delegation policy
(prevents excessive agent spawning for simple tasks).
"""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from core.registry import SkillRegistry
from core.intent import IntentExtractionResult

DELEGATION_NONE = "none"            # Main agent handles task directly (e.g. trivial/simple edit)
DELEGATION_SPECIALIST = "specialist" # Exactly 1 specialized subagent (e.g. deep Spring Boot, Security, QA)
DELEGATION_DUAL = "dual"             # Primary implementer + QA/Security reviewer

@dataclass
class AgentProfile:
    id: str
    name: str
    role: str
    description: str
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    system_prompt: str = ""
    is_ready: bool = True
    missing_skills: List[str] = field(default_factory=list)

@dataclass
class AgentRoutingResult:
    task: str
    delegation_policy: str
    primary_agent: Optional[AgentProfile]
    secondary_agent: Optional[AgentProfile]
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "delegation_policy": self.delegation_policy,
            "primary_agent": self.primary_agent.id if self.primary_agent else "main_agent",
            "primary_role": self.primary_agent.role if self.primary_agent else "Generalist Engineer",
            "secondary_agent": self.secondary_agent.id if self.secondary_agent else None,
            "reasons": self.reasons,
            "warnings": self.warnings
        }

class AgentRegistry:
    def __init__(self, kit_dir: Path):
        self.kit_dir = kit_dir.resolve()
        self.toml_path = self.kit_dir / "agents" / "agents.toml"
        self.skill_registry = SkillRegistry(self.kit_dir)
        self.skill_registry.load_catalog()
        self._agents: Dict[str, AgentProfile] = {}
        self._loaded = False

    def load_agents(self, force: bool = False):
        if self._loaded and not force:
            return

        self._agents.clear()
        if not self.toml_path.exists():
            return

        with open(self.toml_path, "rb") as f:
            data = tomllib.load(f)

        raw_agents = data.get("agents", {})

        for agent_id, info in raw_agents.items():
            req_skills = info.get("skills", [])
            missing = [s for s in req_skills if not self.skill_registry.get_skill(s)]

            profile = AgentProfile(
                id=agent_id,
                name=info.get("name", agent_id),
                role=info.get("role", "Specialist"),
                description=info.get("description", ""),
                skills=req_skills,
                tools=info.get("tools", []),
                system_prompt=info.get("system_prompt", ""),
                is_ready=(len(missing) == 0),
                missing_skills=missing
            )
            self._agents[agent_id] = profile

        self._loaded = True

    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        self.load_agents()
        return self._agents.get(agent_id)

    def list_all(self) -> List[AgentProfile]:
        self.load_agents()
        return list(self._agents.values())

class AgentRouter:
    def __init__(self, kit_dir: Path):
        self.kit_dir = kit_dir.resolve()
        self.agent_registry = AgentRegistry(self.kit_dir)
        self.agent_registry.load_agents()

    def route_agent(
        self,
        task: str,
        intent_analysis: IntentExtractionResult,
        selected_skills: List[str],
        stack_context: Optional[Any] = None
    ) -> AgentRoutingResult:
        task_lower = task.lower()
        all_intents = [intent_analysis.primary_intent] + intent_analysis.secondary_intents
        reasons = []
        warnings = []

        # 1. Check for Trivial Tasks or Casual Chatter (No delegation needed)
        trivial_markers = [
            "typo", "fix typo", "rename variable", "fix spelling", "cap nhat comment", "sua chinh ta",
            "doi ten bien", "copyright", "hello", "xin chao", "joke", "weather", "essay", "just testing"
        ]
        if any(m in task_lower for m in trivial_markers):
            return AgentRoutingResult(
                task=task,
                delegation_policy=DELEGATION_NONE,
                primary_agent=None,
                secondary_agent=None,
                reasons=["Trivial / non-engineering task detected. Executed directly by main agent to conserve tokens."]
            )

        # 2. Score candidate agents based on capability & skill overlap
        candidates: List[Tuple[float, AgentProfile, List[str]]] = []
        for agent in self.agent_registry.list_all():
            if not agent.is_ready:
                warnings.append(f"Agent '{agent.id}' is unavailable due to missing skills: {agent.missing_skills}")
                continue

            score = 0.0
            agent_reasons = []

            # Match agent role and description with detected intents
            desc_lower = f"{agent.role} {agent.description}".lower()

            if "java" in intent_analysis.detected_technologies and agent.id == "java_pro":
                score += 18.0
                agent_reasons.append("JVM / Java engineering match")

            if "python" in intent_analysis.detected_technologies and agent.id == "python_backend":
                score += 18.0
                agent_reasons.append("Python backend engineering match")

            if "airflow" in intent_analysis.detected_technologies and agent.id == "devops_engineer":
                score += 20.0
                agent_reasons.append("Data pipeline / Airflow match")

            if any(k in intent_analysis.detected_technologies for k in ("prometheus", "grafana")) and agent.id == "sre_specialist":
                score += 20.0
                agent_reasons.append("SRE / Metrics match")

            if "duckdb" in intent_analysis.detected_technologies and agent.id == "data_scientist":
                score += 20.0
                agent_reasons.append("Data science / OLAP match")

            if "k6" in intent_analysis.detected_technologies and agent.id == "load_tester":
                score += 20.0
                agent_reasons.append("Load testing match")

            if "playwright" in intent_analysis.detected_technologies and agent.id == "qa_reviewer":
                score += 20.0
                agent_reasons.append("E2E Playwright match")

            if any(f in intent_analysis.detected_technologies for f in ("react", "nextjs", "vue")) and agent.id == "frontend_developer":
                score += 16.0
                agent_reasons.append("Frontend tech stack match")

            if any(k in task_lower for k in ("animation", "drag and drop", "inp", "web vitals")) and agent.id == "frontend_developer":
                score += 15.0
                agent_reasons.append("Frontend UI/UX implementation match")

            if any(k in task_lower for k in ("rate limit", "brute force")) and agent.id == "security_auditor":
                score += 18.0
                agent_reasons.append("Security protection match")

            if any(k in task_lower for k in ("breakout", "container escape", "privilege escalation")) and agent.id == "redteam_security":
                score += 22.0
                agent_reasons.append("Red team security match")

            if any(k in task_lower for k in ("explain analyze", "slow query", "sql", "postgres")) and agent.id == "database_architect":
                score += 18.0
                agent_reasons.append("Database query optimization match")

            if "security" in all_intents and agent.id in ("security_auditor", "redteam_security"):
                score += 14.0
                agent_reasons.append("Application security / threat analysis match")

            if "devops" in all_intents and agent.id in ("devops_engineer", "cloud_architect"):
                score += 12.0
                agent_reasons.append("DevOps / cloud infrastructure match")

            # Match shared skills
            shared = set(selected_skills).intersection(set(agent.skills))
            if shared:
                score += len(shared) * 3.0
                agent_reasons.append(f"Shares curated skills: {', '.join(shared)}")

            if score > 0:
                candidates.append((score, agent, agent_reasons))

        candidates.sort(key=lambda x: x[0], reverse=True)

        if not candidates:
            # Safe default fallback
            return AgentRoutingResult(
                task=task,
                delegation_policy=DELEGATION_NONE,
                primary_agent=None,
                secondary_agent=None,
                reasons=["No specialist persona significantly outperformed generalist. Executing via main agent."]
            )

        primary = candidates[0][1]
        reasons.extend(candidates[0][2])

        # 3. Delegation Policy Evaluation (Single vs Dual specialist)
        secondary = None
        delegation_policy = DELEGATION_SPECIALIST

        # Dual workstream: if task is complex implementation needing separate security or QA review
        if "security" in all_intents and primary.id != "security_auditor":
            sec_agent = self.agent_registry.get_agent("security_auditor")
            if sec_agent and sec_agent.is_ready:
                secondary = sec_agent
                delegation_policy = DELEGATION_DUAL
                reasons.append("Dual delegation: Assigned security_auditor for independent verification gate.")
        elif "testing" in all_intents and primary.id not in ("qa_reviewer", "load_tester"):
            qa_agent = self.agent_registry.get_agent("qa_reviewer")
            if qa_agent and qa_agent.is_ready:
                secondary = qa_agent
                delegation_policy = DELEGATION_DUAL
                reasons.append("Dual delegation: Assigned qa_reviewer for test verification gate.")

        return AgentRoutingResult(
            task=task,
            delegation_policy=delegation_policy,
            primary_agent=primary,
            secondary_agent=secondary,
            reasons=reasons,
            warnings=warnings
        )
