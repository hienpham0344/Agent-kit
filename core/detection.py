"""
Intelligent Project Stack Detection Engine.
Inspects marker files and structural cues without scanning heavy directories (node_modules, .git, etc.).
Returns structured detection results instead of hardcoded 'full'.
"""

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Set

EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "target", ".idea", ".vscode"}

@dataclass
class StackDetectionResult:
    detected_languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    infrastructure: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    recommended_categories: List[str] = field(default_factory=list)
    recommended_preset: str = "minimal"
    explanation: str = ""

def detect_project_stack(target_path: Path) -> StackDetectionResult:
    target_path = target_path.resolve()
    result = StackDetectionResult()

    if not target_path.exists() or not target_path.is_dir():
        result.explanation = "Target directory does not exist or is not a directory."
        result.recommended_preset = "minimal"
        return result

    # Quick inspection of root files and top-level subdirectories (excluding heavy dirs)
    try:
        entries = [e.name for e in target_path.iterdir() if e.name not in EXCLUDE_DIRS]
    except Exception as e:
        result.explanation = f"Error reading directory: {e}"
        return result

    # 1. Java / JVM Markers
    has_maven = "pom.xml" in entries
    has_gradle = any(f in entries for f in ("build.gradle", "build.gradle.kts", "settings.gradle"))
    if has_maven or has_gradle:
        result.detected_languages.append("java")
        evidence = "pom.xml" if has_maven else "build.gradle"
        result.evidence.append(f"JVM build system ({evidence})")

    # 2. Python Markers
    has_pyproject = "pyproject.toml" in entries
    has_requirements = "requirements.txt" in entries
    has_setup_py = "setup.py" in entries
    if has_pyproject or has_requirements or has_setup_py:
        result.detected_languages.append("python")
        evidence = "pyproject.toml" if has_pyproject else ("requirements.txt" if has_requirements else "setup.py")
        result.evidence.append(f"Python project ({evidence})")

    # 3. Node.js & Web Markers
    if "package.json" in entries:
        pkg_file = target_path / "package.json"
        try:
            with open(pkg_file, "r", encoding="utf-8", errors="ignore") as f:
                pkg_data = json.load(f)
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
            
            # Framework inspection
            if "next" in deps:
                result.frameworks.append("nextjs")
                result.evidence.append("Next.js framework in package.json")
            if "react" in deps:
                result.frameworks.append("react")
                result.evidence.append("React library in package.json")
            if "vue" in deps:
                result.frameworks.append("vue")
                result.evidence.append("Vue.js in package.json")
            if "express" in deps or "fastify" in deps or "koa" in deps or "nestjs" in deps:
                result.frameworks.append("node-backend")
                result.evidence.append("Node.js server framework in package.json")

            if any(f in result.frameworks for f in ("react", "nextjs", "vue")):
                result.detected_languages.append("frontend")
            elif "node-backend" in result.frameworks:
                result.detected_languages.append("node")
            else:
                result.detected_languages.append("javascript/typescript")
                result.evidence.append("Node.js package.json")
        except Exception:
            result.detected_languages.append("javascript/typescript")
            result.evidence.append("package.json (unparsed)")

    # 4. Infrastructure / Container Markers
    if "Dockerfile" in entries or "docker-compose.yml" in entries or "docker-compose.yaml" in entries:
        result.infrastructure.append("docker")
        result.evidence.append("Docker containerization")
    if any(e.endswith(".tf") for e in entries) or "terraform" in entries:
        result.infrastructure.append("terraform")
        result.evidence.append("Terraform IaC")
    if "k8s" in entries or "kubernetes" in entries:
        result.infrastructure.append("kubernetes")
        result.evidence.append("Kubernetes manifests")

    # 5. Categorize and Recommend Preset
    categories: Set[str] = {"planning-grilling", "engineering-core", "ops-guardrails"}
    
    is_frontend = "frontend" in result.detected_languages or any(f in result.frameworks for f in ("react", "nextjs", "vue"))
    is_backend = any(l in result.detected_languages for l in ("java", "python", "node")) or "node-backend" in result.frameworks
    is_devops = len(result.infrastructure) > 0

    if is_frontend and is_backend:
        # Fullstack project
        categories.update(["design-uiux", "frontend-mastery", "architecture-domain", "security-threat", "stacks", "web-advanced-graphics"])
        result.recommended_preset = "full"
        result.confidence = 0.95
        result.explanation = f"Detected fullstack multi-language project: {', '.join(result.detected_languages)}."
    elif is_frontend:
        categories.update(["design-uiux", "frontend-mastery", "web-advanced-graphics", "documents-media"])
        result.recommended_preset = "web"
        result.confidence = 0.90
        result.explanation = f"Detected frontend web application: {', '.join(result.frameworks or result.detected_languages)}."
    elif is_backend:
        categories.update(["architecture-domain", "security-threat", "stacks"])
        result.recommended_preset = "backend"
        result.confidence = 0.90
        result.explanation = f"Detected backend application: {', '.join(result.detected_languages)}."
    elif is_devops:
        categories.update(["cloud-infra", "sre-observability", "cloud-aws-gcp-azure", "security-threat"])
        result.recommended_preset = "devops"
        result.confidence = 0.85
        result.explanation = f"Detected DevOps / infrastructure project: {', '.join(result.infrastructure)}."
    else:
        # Unknown or empty project
        result.recommended_preset = "minimal"
        result.confidence = 0.50
        result.explanation = "No explicit language/framework markers detected. Defaulting to minimal core engineering suite."

    result.recommended_categories = sorted(list(categories))
    return result
