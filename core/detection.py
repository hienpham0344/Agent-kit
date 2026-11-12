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
MONOREPO_CONTAINERS = {"apps", "packages", "services", "libs", "modules"}

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

    # Inspect the root, immediate modules, and monorepo sub-packages (apps/*, packages/*).
    try:
        top_dirs = [
            entry for entry in target_path.iterdir()
            if entry.is_dir() and entry.name not in EXCLUDE_DIRS
        ]
        nested_dirs = [
            sub for parent in top_dirs if parent.name in MONOREPO_CONTAINERS
            for sub in parent.iterdir()
            if sub.is_dir() and sub.name not in EXCLUDE_DIRS
        ]
        candidates = [target_path] + top_dirs + nested_dirs
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
        # Inspect pyproject.toml / requirements.txt for AI/LLM or Data/ML cues
        for pdir, pnames in python_projects:
            for dep_file in ("pyproject.toml", "requirements.txt"):
                if dep_file in pnames:
                    dep_text = (pdir / dep_file).read_text(encoding="utf-8", errors="ignore").lower()
                    if any(k in dep_text for k in ("langchain", "langgraph", "openai", "anthropic", "llamaindex", "vllm")):
                        if "ai-llm" not in result.frameworks:
                            result.frameworks.append("ai-llm")
                            result.evidence.append(f"AI/LLM framework in {(pdir / dep_file).relative_to(target_path)}")
                    if any(k in dep_text for k in ("duckdb", "polars", "dbt", "torch", "pytorch", "airflow", "pandas")):
                        if "data-ml" not in result.frameworks:
                            result.frameworks.append("data-ml")
                            result.evidence.append(f"Data/ML tooling in {(pdir / dep_file).relative_to(target_path)}")

    # 2b. Go, Rust, Ruby, PHP, .NET, Mobile Markers
    if any("go.mod" in names for names in entries_by_dir.values()):
        result.detected_languages.append("go")
        result.evidence.append("Go module (go.mod)")
    if any("Cargo.toml" in names for names in entries_by_dir.values()):
        result.detected_languages.append("rust")
        result.evidence.append("Rust crate (Cargo.toml)")
    if any("Gemfile" in names for names in entries_by_dir.values()):
        result.detected_languages.append("ruby")
        result.evidence.append("Ruby project (Gemfile)")
    if any("composer.json" in names for names in entries_by_dir.values()):
        result.detected_languages.append("php")
        result.evidence.append("PHP project (composer.json)")
    if any(any(n.endswith((".csproj", ".sln")) for n in names) for names in entries_by_dir.values()):
        result.detected_languages.append("dotnet")
        result.evidence.append(".NET project (*.csproj/*.sln)")
    if any("pubspec.yaml" in names for names in entries_by_dir.values()):
        result.frameworks.append("flutter")
        result.detected_languages.append("mobile")
        result.evidence.append("Flutter/Dart project (pubspec.yaml)")

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
            if any(name in deps for name in ("svelte", "@angular/core", "astro")) and "frontend-alt" not in result.frameworks:
                result.frameworks.append("frontend-alt")
                result.evidence.append(f"Web framework in {pkg_file.relative_to(target_path)}")
            if any(name in deps for name in ("react-native", "expo")) and "mobile" not in result.frameworks:
                result.frameworks.append("mobile")
                result.evidence.append(f"React Native/Expo in {pkg_file.relative_to(target_path)}")
            if any(name in deps for name in ("three", "@react-three/fiber", "framer-motion", "canvas")) and "graphics" not in result.frameworks:
                result.frameworks.append("graphics")
                result.evidence.append(f"Web graphics/animation in {pkg_file.relative_to(target_path)}")
            if any(name in deps for name in ("express", "fastify", "koa", "nestjs", "@nestjs/core", "hono")) and "node-backend" not in result.frameworks:
                result.frameworks.append("node-backend")
                result.evidence.append(f"Node.js server framework in {pkg_file.relative_to(target_path)}")
            if any(name in deps for name in ("ai", "langchain", "@langchain/core", "openai", "@anthropic-ai/sdk")) and "ai-llm" not in result.frameworks:
                result.frameworks.append("ai-llm")
                result.evidence.append(f"AI/LLM SDK in {pkg_file.relative_to(target_path)}")
            if any(name in deps for name in ("hardhat", "wagmi", "viem", "ethers", "@openzeppelin/contracts")) and "blockchain" not in result.frameworks:
                result.frameworks.append("blockchain")
                result.evidence.append(f"EVM/Web3 tooling in {pkg_file.relative_to(target_path)}")
        except Exception:
            result.evidence.append(f"{pkg_file.relative_to(target_path)} (unparsed)")

    evm_projects = [
        (directory, names) for directory, names in entries_by_dir.items()
        if names.intersection({"hardhat.config.ts", "hardhat.config.js", "foundry.toml"})
    ]
    if evm_projects and "blockchain" not in result.frameworks:
        result.frameworks.append("blockchain")
        directory, names = evm_projects[0]
        marker = next(name for name in ("hardhat.config.ts", "hardhat.config.js", "foundry.toml") if name in names)
        result.evidence.append(f"Smart contracts ({(directory / marker).relative_to(target_path)})")

    if any(framework in result.frameworks for framework in ("react", "nextjs", "vue", "frontend-alt")):
        result.detected_languages.append("frontend")
    if "node-backend" in result.frameworks:
        result.detected_languages.append("node")
    if "blockchain" in result.frameworks:
        result.detected_languages.append("blockchain")
    if node_projects and not any(language in result.detected_languages for language in ("frontend", "node", "mobile")):
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

    is_frontend = "frontend" in result.detected_languages or any(f in result.frameworks for f in ("react", "nextjs", "vue", "frontend-alt"))
    is_backend = any(l in result.detected_languages for l in ("java", "python", "node", "go", "ruby", "php", "dotnet")) or "node-backend" in result.frameworks
    is_mobile = "mobile" in result.detected_languages or "mobile" in result.frameworks or "flutter" in result.frameworks
    is_systems = "rust" in result.detected_languages and not (is_frontend or is_backend)
    is_ai = "ai-llm" in result.frameworks
    is_data = "data-ml" in result.frameworks
    is_devops = len(result.infrastructure) > 0

    if is_frontend and is_backend:
        categories.update(["design-uiux", "frontend-mastery", "architecture-domain", "security-threat", "stacks", "testing-performance"])
        result.recommended_preset = "fullstack"
        result.confidence = 0.95
        result.explanation = f"Detected fullstack multi-language project: {', '.join(result.detected_languages)}."
    elif is_mobile and not is_frontend:
        categories.update(["mobile-crossplatform", "design-uiux"])
        result.recommended_preset = "mobile"
        result.confidence = 0.90
        result.explanation = f"Detected mobile application: {', '.join(result.frameworks or result.detected_languages)}."
    elif is_frontend:
        categories.update(["design-uiux", "frontend-mastery"])
        if "graphics" in result.frameworks:
            categories.add("web-advanced-graphics")
        result.recommended_preset = "web"
        result.confidence = 0.90
        result.explanation = f"Detected frontend web application: {', '.join(result.frameworks or result.detected_languages)}."
    elif is_ai and not is_frontend:
        categories.update(["ai-llm", "stacks"])
        if is_data:
            categories.add("data-ml-analytics")
        result.recommended_preset = "ai"
        result.confidence = 0.90
        result.explanation = f"Detected AI/LLM engineering project: {', '.join(result.detected_languages)}."
    elif is_data and not is_frontend:
        categories.update(["data-ml-analytics", "data-streaming"])
        result.recommended_preset = "data"
        result.confidence = 0.88
        result.explanation = f"Detected Data/ML project: {', '.join(result.detected_languages)}."
    elif is_systems:
        categories.update(["lowlevel-systems", "testing-performance"])
        result.recommended_preset = "systems"
        result.confidence = 0.88
        result.explanation = f"Detected systems engineering project: {', '.join(result.detected_languages)}."
    elif is_backend:
        categories.update(["architecture-domain", "security-threat", "stacks"])
        if is_devops:
            categories.add("cloud-infra")
        result.recommended_preset = "backend"
        result.confidence = 0.90
        result.explanation = f"Detected backend application: {', '.join(result.detected_languages)}."
    elif is_devops:
        categories.update(["cloud-infra", "sre-observability", "cloud-aws-gcp-azure", "security-threat"])
        result.recommended_preset = "devops"
        result.confidence = 0.85
        result.explanation = f"Detected DevOps / infrastructure project: {', '.join(result.infrastructure)}."
    else:
        result.recommended_preset = "minimal"
        result.confidence = 0.50
        result.explanation = "No explicit language/framework markers detected. Defaulting to minimal core engineering suite."

    if "blockchain" in result.frameworks:
        categories.add("security-threat")

    result.recommended_categories = sorted(list(categories))
    return result
