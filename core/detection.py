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

    # Inspect the root and immediate modules (common monorepo layout) only.
    try:
        candidates = [target_path] + [
            entry for entry in target_path.iterdir()
            if entry.is_dir() and entry.name not in EXCLUDE_DIRS
        ]
        entries_by_dir = {
            directory: {entry.name for entry in directory.iterdir()}
            for directory in candidates
        }
    except Exception as e:
        result.explanation = f"Error reading directory: {e}"
        return result

    # 1. Java / JVM Markers
    jvm_projects = [
        (directory, names) for directory, names in entries_by_dir.items()
        if "pom.xml" in names or names.intersection({"build.gradle", "build.gradle.kts", "settings.gradle"})
    ]
    if jvm_projects:
        result.detected_languages.append("java")
        directory, names = jvm_projects[0]
        marker = "pom.xml" if "pom.xml" in names else "build.gradle"
        result.evidence.append(f"JVM build system ({(directory / marker).relative_to(target_path)})")

    # 2. Python Markers
    python_projects = [
        (directory, names) for directory, names in entries_by_dir.items()
        if names.intersection({"pyproject.toml", "requirements.txt", "setup.py"})
    ]
    if python_projects:
        result.detected_languages.append("python")
        directory, names = python_projects[0]
        marker = next(name for name in ("pyproject.toml", "requirements.txt", "setup.py") if name in names)
        result.evidence.append(f"Python project ({(directory / marker).relative_to(target_path)})")

    # 3. Node.js & Web Markers
    node_projects = [directory for directory, names in entries_by_dir.items() if "package.json" in names]
    for directory in node_projects:
        pkg_file = directory / "package.json"
        try:
            with open(pkg_file, "r", encoding="utf-8", errors="ignore") as f:
                pkg_data = json.load(f)
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
            
            # Framework inspection
            if "next" in deps and "nextjs" not in result.frameworks:
                result.frameworks.append("nextjs")
                result.evidence.append(f"Next.js framework in {pkg_file.relative_to(target_path)}")
            if "react" in deps and "react" not in result.frameworks:
                result.frameworks.append("react")
                result.evidence.append(f"React library in {pkg_file.relative_to(target_path)}")
            if "vue" in deps and "vue" not in result.frameworks:
                result.frameworks.append("vue")
                result.evidence.append(f"Vue.js in {pkg_file.relative_to(target_path)}")
            if any(name in deps for name in ("express", "fastify", "koa", "nestjs")) and "node-backend" not in result.frameworks:
                result.frameworks.append("node-backend")
                result.evidence.append(f"Node.js server framework in {pkg_file.relative_to(target_path)}")
        except Exception:
            result.evidence.append(f"{pkg_file.relative_to(target_path)} (unparsed)")

    if any(framework in result.frameworks for framework in ("react", "nextjs", "vue")):
        result.detected_languages.append("frontend")
    if "node-backend" in result.frameworks:
        result.detected_languages.append("node")
    if node_projects and not any(language in result.detected_languages for language in ("frontend", "node")):
        result.detected_languages.append("javascript/typescript")

    # 4. Infrastructure / Container Markers
    entries = entries_by_dir[target_path]
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
        categories.update(["design-uiux", "frontend-mastery", "architecture-domain", "security-threat", "stacks", "testing-performance"])
        result.recommended_preset = "fullstack"
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
