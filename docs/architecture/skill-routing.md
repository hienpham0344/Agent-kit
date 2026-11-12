# Intelligent Skill & Multilingual Routing Architecture (v2)

## 1. Overview
The **Skill Routing Engine v2** provides deterministic, context-aware, multilingual (Vietnamese & English) skill recommendation without requiring external LLM API calls, embeddings, or vector databases.

```mermaid
flowchart TD
    UserQuery["User Task Request<br/>(Vietnamese / English)"] --> Normalize["Unicode Normalization<br/>(Accent Stripping & Sanitization)"]
    Normalize --> IntentEngine["Multilingual Intent Classifier<br/>(Debugging, Testing, Security, Refactoring, etc.)"]
    IntentEngine --> StackContext["Project Context Detection<br/>(Java, Python, React, Docker, Terraform)"]
    
    StackContext --> Scorer["Hybrid Deterministic Scorer<br/>• Name/Alias Overlap (5-6x)<br/>• Frontmatter Triggers (7x)<br/>• Intent Alignment (6-8x)<br/>• Stack Tokens (4-5x)"]
    
    Scorer --> DepResolver["Dependency & Conflict Resolution"]
    DepResolver --> DecisionPolicy{"Confidence Decision Policy"}
    
    DecisionPolicy -- "Score >= 12.0" --> AutoSelect["auto_select (High Confidence)"]
    DecisionPolicy -- "Score 5.0 - 11.9" --> Recommend["recommend (Top Candidates)"]
    DecisionPolicy -- "Score < 5.0" --> Clarify["clarification_required"]
    DecisionPolicy -- "Chatter / Negative" --> NoMatch["no_match (Zero Context Wasted)"]
```

---

## 2. Progressive Disclosure (3-Level Loading)
1. **Level 1 (Discovery)**: Minimal frontmatter indexing (`name`, `description`, `category`, `tags`). Scanning all 285 skills takes $<10\text{ ms}$.
2. **Level 2 (Selection)**: Ranking candidates using intent and project markers without touching skill bodies.
3. **Level 3 (Execution Preparation)**: Loading complete `SKILL.md` body on-demand only for the top selected skills.

---

## 3. Multilingual Support (English & Vietnamese)
The engine normalizes diacritics and technical synonyms:
- `"Sửa lỗi xác thực JWT trong Spring Boot"` $\to$ Intent: `debugging` + `security`, Tech: `spring` $\to$ Activates `jwt-vulnerabilities-remediation` and `systematic-debugging`.
- `"Đăng nhập bị lỗi 401, tìm nguyên nhân"` $\to$ Intent: `debugging` + `security` $\to$ Activates `systematic-debugging`.
