"""
Standard Presets Definition for Agents-kit.
Ensures 100% synchronization between README documentation, CLI help, and skills catalog.
"""

from typing import Dict, List

CONTEXT_BUDGET_WARN = 125
CONTEXT_BUDGET_CRITICAL = 180

PRESETS: Dict[str, List[str]] = {
    "fullstack": [
        "planning-grilling",
        "engineering-core",
        "architecture-domain",
        "design-uiux",
        "security-threat",
        "stacks",
        "ops-guardrails",
        "testing-performance",
        "frontend-mastery",
    ],
    "full": [
        "planning-grilling",
        "engineering-core",
        "architecture-domain",
        "design-uiux",
        "security-threat",
        "stacks",
        "ops-guardrails",
        "documents-media",
        "ai-llm",
        "cloud-infra",
        "testing-performance",
        "mobile-crossplatform",
        "data-streaming",
        "sre-observability",
        "data-ml-analytics",
        "web-advanced-graphics",
        "security-redteam",
        "lowlevel-systems",
        "cloud-aws-gcp-azure",
        "developer-productivity",
        "frontend-mastery",
    ],
    "web": [
        "planning-grilling",
        "engineering-core",
        "design-uiux",
        "documents-media",
        "ops-guardrails",
        "web-advanced-graphics",
        "frontend-mastery",
    ],
    "backend": [
        "planning-grilling",
        "engineering-core",
        "architecture-domain",
        "security-threat",
        "stacks",
        "ops-guardrails",
    ],
    "ai": [
        "planning-grilling",
        "engineering-core",
        "ai-llm",
        "stacks",
        "ops-guardrails",
    ],
    "mobile": [
        "planning-grilling",
        "engineering-core",
        "mobile-crossplatform",
        "design-uiux",
        "ops-guardrails",
    ],
    "data": [
        "planning-grilling",
        "engineering-core",
        "data-ml-analytics",
        "data-streaming",
        "ops-guardrails",
    ],
    "systems": [
        "planning-grilling",
        "engineering-core",
        "lowlevel-systems",
        "testing-performance",
        "ops-guardrails",
    ],
    "devops": [
        "ops-guardrails",
        "security-threat",
        "cloud-infra",
        "sre-observability",
        "cloud-aws-gcp-azure",
        "engineering-core",
    ],
    "security": [
        "security-threat",
        "security-redteam",
        "ops-guardrails",
        "engineering-core",
    ],
    "minimal": [
        "planning-grilling",
        "engineering-core",
        "ops-guardrails",
    ]
}

PRESET_DESCRIPTIONS: Dict[str, str] = {
    "auto": "Intelligently inspects project files to install stack-specific skills",
    "fullstack": "Frontend and backend engineering without unrelated specialist domains",
    "full": "All 21 domains (warning: large catalog may exceed AI host context skill budget)",
    "web": "Frontend, UI/UX, Web APIs, and browser graphics",
    "backend": "Architecture, Domain modeling, JVM/Python/Node stacks, Security threats",
    "ai": "LLM workflows, RAG, prompt evals, vector DBs, and guardrails",
    "mobile": "React Native, Expo, Flutter, offline sync, and mobile UI/UX",
    "data": "DuckDB, Polars, dbt, Kafka, Airflow, and PyTorch analytics",
    "systems": "Rust/WASM, C/C++ memory safety, Linux eBPF, and performance profiling",
    "devops": "Cloud infrastructure, SRE observability, AWS/GCP/Azure, Ops guardrails",
    "security": "Threat modeling, OWASP mitigation, SAST, Penetration testing & Red teaming",
    "minimal": "Essential TDD, systematic debugging, basic planning, and core guardrails"
}
