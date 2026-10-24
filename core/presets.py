"""
Standard Presets Definition for Agents-kit.
Ensures 100% synchronization between README documentation, CLI help, and skills catalog.
"""

from typing import Dict, List

PRESETS: Dict[str, List[str]] = {
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
    "full": "All 21 domains (285 skills, 22 subagents, 10 runbooks, 18 templates, 6 cookbooks)",
    "web": "Frontend, UI/UX, Web APIs, and browser graphics",
    "backend": "Architecture, Domain modeling, JVM/Python/Node stacks, Security threats",
    "devops": "Cloud infrastructure, SRE observability, AWS/GCP/Azure, Ops guardrails",
    "security": "Threat modeling, OWASP mitigation, SAST, Penetration testing & Red teaming",
    "minimal": "Essential TDD, systematic debugging, basic planning, and core guardrails"
}
