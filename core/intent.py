"""
Multilingual Intent Recognition Engine (English & Vietnamese).
Extracts engineering intents, frameworks, languages, actions, and entities from user task requests.
Uses Unicode normalization and technical terminology synonyms without requiring external LLM APIs.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple

# Mapping engineering intents to multilingual keywords (English & Vietnamese)
INTENT_PATTERNS: Dict[str, List[str]] = {
    "debugging": [
        "debug", "fix", "error", "failing", "failure", "crash", "bug", "trace", "slow", "broken",
        "exception", "issue", "investigate", "stacktrace", "root cause",
        # Vietnamese
        "sua loi", "loi", "khong chay", "bi loi", "hong", "tim nguyen nhan", "dieu tra",
        "truy vet", "khac phuc", "cham", "do", "bi crash", "ngoai le"
    ],
    "testing": [
        "test", "testing", "unit test", "integration", "e2e", "tdd", "mock", "regression",
        "benchmark", "assert", "coverage", "verify",
        # Vietnamese
        "kiem thu", "kiem tra", "viet test", "viet unit test", "kiem thu hoi quy", "xac minh"
    ],
    "security": [
        "auth", "authentication", "authorization", "jwt", "token", "password", "security",
        "threat", "vulnerability", "csrf", "xss", "cors", "secret", "permission", "oauth",
        "login", "session", "401", "403", "unauthorized", "forbidden", "sast",
        # Vietnamese
        "xac thuc", "phan quyen", "bao mat", "lo hong", "mat khau", "dang nhap",
        "dang ky", "trao quyen", "mat ma", "bi cam"
    ],
    "feature": [
        "build", "create", "implement", "add", "develop", "generate", "feature", "new",
        # Vietnamese
        "xay dung", "tao", "them", "phat trien", "viet moi", "chuc nang", "tinh nang"
    ],
    "refactoring": [
        "refactor", "clean code", "simplify", "restructure", "optimize", "rewrite",
        # Vietnamese
        "tai cau truc", "toi uu", "lam sach code", "viet lai", "don dep"
    ],
    "architecture": [
        "architecture", "design", "domain", "ddd", "system design", "spec", "srs", "adr",
        # Vietnamese
        "kien truc", "thiet ke", "dac ta", "mo hinh hoa"
    ],
    "database": [
        "database", "db", "sql", "postgres", "mysql", "sqlite", "query", "migration", "schema",
        "table", "index", "orm", "prisma", "hibernate",
        # Vietnamese
        "co so du lieu", "truy van", "bang", "di cu"
    ],
    "devops": [
        "docker", "container", "kubernetes", "k8s", "terraform", "ci", "cd", "pipeline",
        "deploy", "aws", "gcp", "azure", "helm",
        # Vietnamese
        "trien khai", "ha tang", "dong goi"
    ],
    "review": [
        "review", "audit", "inspect", "check", "evaluate",
        # Vietnamese
        "danh gia", "kiem tra code", "soat loi", "ra soat"
    ]
}

TECH_SYNONYMS: Dict[str, str] = {
    "spring": "spring",
    "spring boot": "spring",
    "springboot": "spring",
    "react": "react",
    "reactjs": "react",
    "next": "nextjs",
    "nextjs": "nextjs",
    "next.js": "nextjs",
    "vue": "vue",
    "vuejs": "vue",
    "fastapi": "fastapi",
    "django": "django",
    "python": "python",
    "pytest": "python",
    "java": "java",
    "jvm": "java",
    "postgres": "postgres",
    "postgresql": "postgres",
    "sql": "database",
    "k8s": "kubernetes",
    "k8": "kubernetes",
    "airflow": "airflow",
    "prometheus": "prometheus",
    "grafana": "grafana",
    "duckdb": "duckdb",
    "k6": "k6",
    "playwright": "playwright",
    "redis": "redis"
}

def remove_vietnamese_accents(text: str) -> str:
    """Normalize Vietnamese text to non-accented ASCII representation."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    # Replace special Vietnamese chars like đ, Đ
    text = text.replace('đ', 'd').replace('Đ', 'd')
    return text.lower()

@dataclass
class IntentExtractionResult:
    original_text: str
    normalized_text: str
    primary_intent: str
    secondary_intents: List[str] = field(default_factory=list)
    detected_technologies: List[str] = field(default_factory=list)
    tokens: Set[str] = field(default_factory=set)

def extract_intents(task_description: str) -> IntentExtractionResult:
    """Analyze and extract multilingual intents and entities from a software engineering task."""
    raw = task_description.strip()
    norm_no_accents = remove_vietnamese_accents(raw)
    
    # Combined search corpus (both original lowercased and stripped of accents)
    corpus = f"{raw.lower()} {norm_no_accents}"

    # Extract tokens
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", norm_no_accents)
    tokens = set(words)

    # Score intents
    intent_scores: Dict[str, float] = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0.0
        for pat in patterns:
            if re.search(r"\b" + re.escape(pat) + r"\b", corpus):
                score += 2.0
            elif pat in corpus:
                score += 1.0
        if score > 0:
            intent_scores[intent] = score

    # Determine primary and secondary intents
    sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_intents[0][0] if sorted_intents else "feature"
    secondary = [item[0] for item in sorted_intents[1:] if item[1] >= 1.0]

    # Detect technologies
    detected_techs = set()
    for tech_token, canonical in TECH_SYNONYMS.items():
        if re.search(r"\b" + re.escape(tech_token) + r"\b", corpus):
            detected_techs.add(canonical)

    return IntentExtractionResult(
        original_text=raw,
        normalized_text=norm_no_accents,
        primary_intent=primary,
        secondary_intents=secondary,
        detected_technologies=sorted(list(detected_techs)),
        tokens=tokens
    )
