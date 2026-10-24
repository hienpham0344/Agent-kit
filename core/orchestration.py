"""
Task Lifecycle and Orchestration Planning Engine.
Implements dependency-aware task decomposition, explicit lifecycle state transitions,
verification gates, and structured execution plans.
"""

from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any, Set

class TaskState(Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"

@dataclass
class TaskStep:
    id: str
    title: str
    assigned_agent: str
    required_skills: List[str]
    dependencies: List[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    verification_command: Optional[str] = None
    output_artifacts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

@dataclass
class OrchestrationPlan:
    task: str
    steps: List[TaskStep]
    estimated_context_tokens: int = 0
    delegation_summary: str = ""

    def validate_dependencies(self) -> List[str]:
        """Detect circular dependencies or missing step references."""
        errors = []
        step_ids = {s.id for s in self.steps}
        for s in self.steps:
            for dep in s.dependencies:
                if dep not in step_ids:
                    errors.append(f"Step '{s.id}' depends on non-existent step '{dep}'")

        # Detect cycle
        visited = {}
        def dfs(node: str, path: List[str]):
            visited[node] = 1
            path.append(node)
            step_obj = next((st for st in self.steps if st.id == node), None)
            if step_obj:
                for dep in step_obj.dependencies:
                    if dep in step_ids:
                        if visited.get(dep) == 1:
                            errors.append(f"Circular task dependency detected: {' -> '.join(path + [dep])}")
                        elif visited.get(dep, 0) == 0:
                            dfs(dep, path)
            path.pop()
            visited[node] = 2

        for sid in step_ids:
            if visited.get(sid, 0) == 0:
                dfs(sid, [])

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "delegation_summary": self.delegation_summary,
            "steps": [
                {
                    "id": s.id,
                    "title": s.title,
                    "agent": s.assigned_agent,
                    "skills": s.required_skills,
                    "dependencies": s.dependencies,
                    "state": s.state.value,
                    "verification": s.verification_command
                }
                for s in self.steps
            ]
        }

class OrchestrationEngine:
    def __init__(self, kit_dir: Path):
        self.kit_dir = kit_dir.resolve()

    def decompose_task(
        self,
        task: str,
        primary_agent: str = "main_agent",
        secondary_agent: Optional[str] = None,
        selected_skills: Optional[List[str]] = None
    ) -> OrchestrationPlan:
        """Decompose a high-level task into a dependency-aware plan with verification gates."""
        skills = selected_skills or []
        steps: List[TaskStep] = []

        # Step 1: Requirements & Plan Analysis
        steps.append(TaskStep(
            id="step-1-analysis",
            title="Analyze requirements & system design",
            assigned_agent="system_coordinator" if primary_agent != "main_agent" else "main_agent",
            required_skills=[s for s in skills if "planning" in s or "architecture" in s] or ["systematic-debugging"],
            dependencies=[]
        ))

        # Step 2: Implementation (TDD first)
        steps.append(TaskStep(
            id="step-2-implementation",
            title="Implement code changes & unit tests",
            assigned_agent=primary_agent,
            required_skills=skills,
            dependencies=["step-1-analysis"],
            verification_command="python3 -m unittest discover tests/"
        ))

        # Step 3: Independent QA or Security Review (if secondary agent assigned)
        if secondary_agent:
            steps.append(TaskStep(
                id="step-3-review",
                title=f"Independent verification by {secondary_agent}",
                assigned_agent=secondary_agent,
                required_skills=[s for s in skills if "security" in s or "test" in s] or ["verification-before-completion"],
                dependencies=["step-2-implementation"],
                verification_command="git diff"
            ))

        plan = OrchestrationPlan(
            task=task,
            steps=steps,
            delegation_summary=f"Primary: {primary_agent}" + (f", Reviewer: {secondary_agent}" if secondary_agent else "")
        )
        return plan
