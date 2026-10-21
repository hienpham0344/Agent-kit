<div align="center">

# 🛠️ Agents-Kit: The Autonomous AI Engineering Hub

**Production-grade repository of 253 Curated Skills, 22 Specialized Subagents, Built-in Developer Tools, 10 Production MCP Servers, 9 Enterprise SDLC Workflows, and 18 Production Templates for Antigravity, Claude Code, GitHub Copilot, Cursor, and Windsurf.**

[![Skills Count](https://img.shields.io/badge/Skills-253%20Curated-blue.svg?style=flat-square)](skills/)
[![Subagents](https://img.shields.io/badge/Subagents-22%20Personas-purple.svg?style=flat-square)](agents/)
[![Developer Tools](https://img.shields.io/badge/Tools-CLI%20%26%20MCP-red.svg?style=flat-square)](tools/)
[![MCP Servers](https://img.shields.io/badge/MCP%20Servers-10%20Integrated-success.svg?style=flat-square)](mcp/)
[![Workflows](https://img.shields.io/badge/Workflows-9%20Runbooks-orange.svg?style=flat-square)](workflows/recipes/)
[![Templates](https://img.shields.io/badge/Templates-18%20Production-green.svg?style=flat-square)](workflows/templates/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

## 🧰 Built-in Developer Tools & MCP Ecosystem

Agents-kit is equipped with an integrated CLI toolkit and MCP server hub:

```bash
# Search skills and descriptions instantly
agents-kit search <query>

# Discover, verify, and inspect MCP servers
agents-kit mcp
agents-kit mcp verify context-mode

# Scaffold a new spec-compliant skill
agents-kit create-skill my-skill-name --domain engineering-core

# Analyze token footprint for prompts or files
python3 tools/token_estimator.py path/to/file.py

# AST-based code complexity & function signature scanner
python3 tools/ast_analyzer.py path/to/project/

# Run the complete test suite
agents-kit test
```

### Integrated Production MCP Servers (`mcp/servers.json`)
1. **`context-mode`**: FTS5 SQLite sandbox execution for token-saving bash piping and searches.
2. **`filesystem`**: Scoped secure file inspection and traversal.
3. **`postgres`**: Real-time relational database schema profiling and read queries.
4. **`sqlite`**: Local SQLite querying and table inspections.
5. **`github`**: GitHub PRs, issues, commits, and repository search.
6. **`puppeteer`**: Headless browser automation, visual snapshots, and console monitoring.
7. **`memory`**: Graph-based persistent agent memory across sessions.
8. **`brave-search`**: Live web search and documentation retrieval.
9. **`docker`**: Container inspection and lifecycle orchestration.
10. **`sentry`**: Production exception and breadcrumb querying.

---

## 🤖 22 Specialist Subagents (`agents.toml`)

| Subagent Name | Role | Core Skills & Focus |
| :--- | :--- | :--- |
| **`system_coordinator`** | Technical Planner & SRS Author | `srs-authoring`, `wayfinder`, `grill-me`, `to-spec`, `to-tickets` |
| **`database_architect`** | Database Architect & Data Modeler | `database-design`, `domain-modeling`, `codebase-design`, ERDs |
| **`devops_engineer`** | DevOps & Cloud Deployment Engineer | `docker-and-containerization`, `cloud-and-production-deploy`, `git-conflict-resolution` |
| **`frontend_architect`** | Frontend Architect & System Planner | `ui-ux-pro-max`, `design-system`, `codebase-design`, `writing-plans` |
| **`ui_ux_designer`** | UI/UX Intelligence Specialist | `ui-ux-pro-max`, `design-system`, `ui-styling`, `frontend-ui-engineering` |
| **`taste_craftsman`** | Anti-Slop Art Director & Polish | `design-taste-frontend`, `minimalist-ui`, `industrial-brutalist-ui` |
| **`frontend_developer`**| Frontend Component Implementer | `frontend-ui-engineering`, `test-driven-development`, `web-performance` |
| **`qa_reviewer`** | QA, Accessibility & Code Reviewer | `verification-before-completion`, `code-review-excellence`, `systematic-debugging` |
| **`web_performance_auditor`**| Web Vitals & Frontend Auditor | `web-performance`, `verification-before-completion` |
| **`java_pro`** | Java & JVM Specialist | `java-spring-boot`, `systematic-debugging`, `error-handling-patterns` |
| **`python_backend`** | Python Backend Specialist | `python-backend`, `test-driven-development`, `systematic-debugging` |
| **`security_auditor`** | Application Security & Threat Modeling | `security-threat-modeling`, `stride-analysis-patterns`, `attack-tree-construction` |
| **`ai_engineer`** | AI & LLM Systems Engineer | `rag-evaluation`, `prompt-engineering-evals`, `vector-database-ops`, `llm-observability-tracing` |
| **`cloud_architect`** | Cloud Infrastructure & Serverless | `terraform-modular-iac`, `cloudflare-workers-pages`, `cloudflare-d1-kv`, `supabase-migrations-rls` |
| **`sre_specialist`** | SRE & Observability Specialist | `datadog-apm-tracing`, `prometheus-grafana-metrics`, `sentry-error-tracking-triage`, `slo-monitoring` |
| **`mobile_dev`** | Mobile & Cross-Platform Engineer | `react-native-expo-architecture`, `expo-eas-ci-cd-builds`, `mobile-offline-first-sync`, `hermes` |
| **`load_tester`** | Performance & Chaos Load Tester | `k6-high-concurrency-testing`, `locust-distributed-load-testing`, `chaos-resilience`, `profiling` |
| **`data_scientist`** | Data Scientist & ML Engineer | `duckdb-in-memory-analytics`, `polars-high-performance-df`, `dbt-data-transformations`, `pytorch` |
| **`redteam_security`** | Offensive Security & Red Team | `owasp-top-10-mitigation`, `penetration-testing-playbook`, `container-escape-breakout-defense` |
| **`systems_engineer`** | Low-Level Systems & Performance | `webassembly-rust-wasm`, `c-modern-memory-safety`, `cpp-modern-raii-concurrency`, `linux-ebpf` |
| **`graphics_web_dev`** | Interactive Graphics & WebGL | `threejs-webgl-3d`, `webrtc-peer-to-peer-streaming`, `websocket-realtime-collaboration`, `tauri` |
| **`cloud_platform_lead`**| Multi-Cloud Platform Lead | `aws-eks-managed-kubernetes`, `aws-dynamodb-single-table-design`, `gcp-bigquery`, `azure-aks` |

---

## 📚 20 Curated Skill Domains (253 Skills Total)

1. **`skills/planning-grilling/` (10 Skills)**: Idea refinement, SRS IEEE 830, technical grilling, wayfinder.
2. **`skills/architecture-domain/` (10 Skills)**: Clean architecture, SOLID, domain modeling, design patterns.
3. **`skills/engineering-core/` (10 Skills)**: TDD, systematic debugging, code review, subagent development.
4. **`skills/design-uiux/` (10 Skills)**: Design-taste anti-slop, UI/UX Pro Max, brutalist, brandkit, stitch.
5. **`skills/security-threat/` (10 Skills)**: STRIDE threat modeling, attack trees, SAST, content sanitization.
6. **`skills/stacks/` (10 Skills)**: Java Spring Boot, Python, Fullstack meta-frameworks, Golang, Rust, C#, Node.
7. **`skills/ops-guardrails/` (10 Skills)**: Context engineering, Docker, CI/CD, Git conflict resolution, semver.
8. **`skills/documents-media/` (15 Skills)**: README creation, Generative UI, image-to-code, full output rules.
9. **`skills/ai-llm/` (14 Skills)**: RAG evals, prompt matrices, vector DBs, LangGraph, OpenLLMetry tracing.
10. **`skills/cloud-infra/` (14 Skills)**: Terraform modular IaC, Cloudflare edge, Supabase RLS, Helm, Vault.
11. **`skills/testing-performance/` (12 Skills)**: k6 concurrency, Locust swarm, chaos mesh, Playwright E2E.
12. **`skills/mobile-crossplatform/` (10 Skills)**: React Native Expo Router, EAS CI/CD, offline sync, Hermes.
13. **`skills/data-streaming/` (10 Skills)**: Kafka streams, Redis distributed caching & Redlock, ClickHouse OLAP.
14. **`skills/sre-observability/` (8 Skills)**: Datadog APM, Prometheus metrics, Sentry error triage, SLO burn rates.
15. **`skills/data-ml-analytics/` (17 Skills)**: DuckDB in-memory, Polars lazy frames, dbt transforms, PyTorch, Airflow DAGs.
16. **`skills/web-advanced-graphics/` (17 Skills)**: Three.js WebGL 3D, WebRTC, Framer Motion, Tauri, Electron security.
17. **`skills/security-redteam/` (17 Skills)**: OWASP Top 10, pentesting playbooks, container escapes, TruffleHog.
18. **`skills/lowlevel-systems/` (16 Skills)**: WebAssembly Rust, C memory safety, C++ RAII, eBPF tracing, io_uring.
19. **`skills/cloud-aws-gcp-azure/` (17 Skills)**: AWS EKS & DynamoDB, GCP BigQuery & Spanner, Azure AKS & Entra ID.
20. **`skills/developer-productivity/` (16 Skills)**: Git reflog/bisect, worktrees, strict Bash, AST grep, jq/yq.

---

## ⚡ Global Installation & CLI Usage

```bash
# Clone to your local workspace
git clone https://github.com/hienpham0344/Agent-kit.git ~/Project/Agents-kit

# Enable global CLI command
cd ~/Project/Agents-kit
./bin/agents-kit setup-env
source ~/.bashrc

# Run system & health check
agents-kit doctor
```

Install into any software project:
```bash
cd /path/to/your/project
agents-kit install . --preset full
agents-kit doctor
```
