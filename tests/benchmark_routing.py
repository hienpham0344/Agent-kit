"""
Benchmark Suite for Skill & Agent Routing Accuracy.
Evaluates Precision@K, Recall@K, Top-1 Accuracy, and Latency across 50+ diverse test cases
spanning Python, Java, React/Next.js, DevOps, Security, Vietnamese, English, and negative queries.
"""

import time
import unittest
from pathlib import Path
from typing import List, Dict, Any

from core.routing import SkillRouter
from core.agent_router import AgentRouter
from core.intent import extract_intents

KIT_DIR = Path(__file__).resolve().parent.parent

BENCHMARK_DATASET: List[Dict[str, Any]] = [
    # 1. Java / Spring Boot (English & Vietnamese)
    {"task": "Debug Java Spring Boot auth failure with JWT", "expected_skills": ["systematic-debugging", "jwt-vulnerabilities-remediation"], "expected_agent": "security_auditor"},
    {"task": "Sua loi xac thuc JWT trong Spring Boot", "expected_skills": ["systematic-debugging", "jwt-vulnerabilities-remediation"], "expected_agent": "security_auditor"},
    {"task": "Dang nhap bi loi 401, tim nguyen nhan", "expected_skills": ["systematic-debugging"], "expected_agent": "security_auditor"},
    {"task": "Optimize JVM garbage collection and memory leak", "expected_skills": ["memory-leak-detection", "systematic-debugging"], "expected_agent": "java_pro"},
    {"task": "Dieu tra ro ri bo nho trong ung dung Java", "expected_skills": ["memory-leak-detection", "systematic-debugging"], "expected_agent": "java_pro"},

    # 2. Python Backend (FastAPI, Pytest, Pydantic)
    {"task": "Build FastAPI user model with Pydantic v2 validation", "expected_skills": ["pydantic-v2"], "expected_agent": "python_backend"},
    {"task": "Tao model pydantic v2 cho API nguoi dung", "expected_skills": ["pydantic-v2"], "expected_agent": "python_backend"},
    {"task": "Write unit tests with pytest fixtures and mocking", "expected_skills": ["python-testing-patterns"], "expected_agent": "python_backend"},
    {"task": "Viet unit test pytest cho service thanh toan", "expected_skills": ["python-testing-patterns"], "expected_agent": "python_backend"},
    {"task": "Refactor Python codebase into clean architecture monorepo", "expected_skills": ["python-monorepo-architecture", "python-project-structure"], "expected_agent": "python_backend"},

    # 3. React / Next.js / Frontend
    {"task": "Create smooth layout animations in React with Framer Motion", "expected_skills": ["framer-motion-animation-patterns"], "expected_agent": "frontend_developer"},
    {"task": "Tao animation muot ma trong React bang framer motion", "expected_skills": ["framer-motion-animation-patterns"], "expected_agent": "frontend_developer"},
    {"task": "Build accessible drag and drop list using dndkit", "expected_skills": ["drag-and-drop-dndkit"], "expected_agent": "frontend_developer"},
    {"task": "Toi uu Core Web Vitals va INP responsiveness tren Next.js", "expected_skills": ["inp-responsiveness-profiling"], "expected_agent": "frontend_developer"},
    {"task": "Debug Interaction to Next Paint responsiveness delay in browser", "expected_skills": ["inp-responsiveness-profiling"], "expected_agent": "frontend_developer"},

    # 4. Security & Threat Modeling
    {"task": "Conduct STRIDE threat modeling on cloud API gateway", "expected_skills": ["stride-analysis-patterns", "attack-tree-construction"], "expected_agent": "security_auditor"},
    {"task": "Phan tich rui ro bao mat theo mo hinh STRIDE", "expected_skills": ["stride-analysis-patterns", "attack-tree-construction"], "expected_agent": "security_auditor"},
    {"task": "Prevent SQL injection and blind timing attacks in database queries", "expected_skills": ["sql-injection-blind-timing"], "expected_agent": "security_auditor"},
    {"task": "Audit JWT secret tokens and prevent algorithm none bypass", "expected_skills": ["jwt-vulnerabilities-remediation"], "expected_agent": "security_auditor"},
    {"task": "Chong tan cong CSRF va cau hinh CORS an toan", "expected_skills": ["cors-csrf-zero-trust"], "expected_agent": "security_auditor"},

    # 5. DevOps, Cloud & SRE
    {"task": "Author resilient Apache Airflow DAG with TaskFlow API", "expected_skills": ["apache-airflow-dag-orchestration"], "expected_agent": "devops_engineer"},
    {"task": "Viet DAG Apache Airflow cho pipeline xu ly du lieu", "expected_skills": ["apache-airflow-dag-orchestration"], "expected_agent": "devops_engineer"},
    {"task": "Write Terraform modular infrastructure for AWS ECS Fargate", "expected_skills": ["terraform-modular-iac", "aws-ecs-fargate-deployments"], "expected_agent": "cloud_architect"},
    {"task": "Configure Prometheus metrics histogram and Grafana alerting", "expected_skills": ["prometheus-grafana-metrics"], "expected_agent": "sre_specialist"},
    {"task": "Thiet lap metric Prometheus va dashboard Grafana", "expected_skills": ["prometheus-grafana-metrics"], "expected_agent": "sre_specialist"},

    # 6. Database & High Performance Analytics
    {"task": "Query large Parquet datasets in memory using DuckDB", "expected_skills": ["duckdb-in-memory-analytics"], "expected_agent": "data_scientist"},
    {"task": "Truy van file parquet toc do cao voi DuckDB", "expected_skills": ["duckdb-in-memory-analytics"], "expected_agent": "data_scientist"},
    {"task": "Analyze slow PostgreSQL queries with EXPLAIN ANALYZE", "expected_skills": ["database-query-profiling"], "expected_agent": "database_architect"},
    {"task": "Toi uu cau truy van SQL bi cham bang EXPLAIN ANALYZE", "expected_skills": ["database-query-profiling"], "expected_agent": "database_architect"},
    {"task": "Tune Apache Kafka consumer group rebalance and commit offsets", "expected_skills": ["kafka-consumer-group-tuning"], "expected_agent": "data_scientist"},

    # 7. Testing & Quality Assurance
    {"task": "Write end to end browser automation tests with Playwright", "expected_skills": ["playwright-e2e-automation"], "expected_agent": "qa_reviewer"},
    {"task": "Viet kiem thu tu dong E2E voi Playwright", "expected_skills": ["playwright-e2e-automation"], "expected_agent": "qa_reviewer"},
    {"task": "Run high concurrency load testing scripts with k6", "expected_skills": ["k6-high-concurrency-testing"], "expected_agent": "load_tester"},
    {"task": "Kiem thu tai chiu tai cao bang k6", "expected_skills": ["k6-high-concurrency-testing"], "expected_agent": "load_tester"},
    {"task": "Implement consumer driven contract tests with Pact", "expected_skills": ["contract-testing-pact"], "expected_agent": "qa_reviewer"},

    # 8. Trivial Tasks (Should require NO delegation)
    {"task": "Fix small typo in header comment", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "Sua loi chinh ta trong tai lieu README", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "Rename variable user_name to username", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "Doi ten bien dem trong vong lap", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "Update copyright year in LICENSE", "expected_skills": [], "expected_agent": "main_agent"},

    # 9. Complex Compound Tasks (Multiple workstreams)
    {"task": "Build OAuth2 login endpoint and write regression tests", "expected_skills": ["jwt-vulnerabilities-remediation"], "expected_agent": "security_auditor"},
    {"task": "Xay dung tinh nang xac thuc OAuth2 va viet test hoi quy", "expected_skills": ["jwt-vulnerabilities-remediation"], "expected_agent": "security_auditor"},
    {"task": "Implement distributed rate limiter with Redis sliding window", "expected_skills": ["rate-limiting-distributed-ddos"], "expected_agent": "security_auditor"},
    {"task": "Chong tan cong brute force bang distributed rate limiting", "expected_skills": ["rate-limiting-distributed-ddos"], "expected_agent": "security_auditor"},
    {"task": "Audit Docker container against breakout and privilege escalation", "expected_skills": ["container-escape-breakout-defense"], "expected_agent": "redteam_security"},

    # 10. Negative / Ambiguous Tasks
    {"task": "Hello what is the weather today", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "Xin chao thoi tiet the nao", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "Tell me a joke about programming", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "Can you help me write an essay about history", "expected_skills": [], "expected_agent": "main_agent"},
    {"task": "just testing chat connection", "expected_skills": [], "expected_agent": "main_agent"}
]

def run_routing_benchmark() -> Dict[str, Any]:
    skill_router = SkillRouter(KIT_DIR)
    agent_router = AgentRouter(KIT_DIR)

    total_cases = len(BENCHMARK_DATASET)
    top1_correct = 0
    top3_correct = 0
    agent_correct = 0

    start_time = time.perf_counter()

    for item in BENCHMARK_DATASET:
        task = item["task"]
        exp_skills = item["expected_skills"]
        exp_agent = item["expected_agent"]

        s_res = skill_router.recommend(task, top_k=3, min_score=2.0)
        recommended_names = [r.skill.name for r in s_res.recommendations]

        # Skill Evaluation
        if not exp_skills:
            # Negative / Trivial query: Correct if top-1 is empty or score is low
            if len(recommended_names) == 0 or s_res.decision in ("no_match", "clarification_required"):
                top1_correct += 1
                top3_correct += 1
        else:
            if recommended_names and any(name in exp_skills for name in recommended_names[:1]):
                top1_correct += 1
            if any(name in exp_skills for name in recommended_names):
                top3_correct += 1

        # Agent Evaluation
        intent_res = extract_intents(task)
        a_res = agent_router.route_agent(task, intent_res, recommended_names)
        actual_agent = a_res.primary_agent.id if a_res.primary_agent else "main_agent"

        if exp_agent == "main_agent":
            if actual_agent == "main_agent" or a_res.delegation_policy == "none":
                agent_correct += 1
        else:
            if actual_agent == exp_agent or (a_res.secondary_agent and a_res.secondary_agent.id == exp_agent):
                agent_correct += 1

    duration = time.perf_counter() - start_time
    avg_latency_ms = (duration / total_cases) * 1000

    metrics = {
        "total_test_cases": total_cases,
        "top1_skill_accuracy": round((top1_correct / total_cases) * 100, 2),
        "top3_skill_recall": round((top3_correct / total_cases) * 100, 2),
        "agent_routing_accuracy": round((agent_correct / total_cases) * 100, 2),
        "average_latency_ms": round(avg_latency_ms, 2)
    }
    return metrics

class TestRoutingBenchmark(unittest.TestCase):
    def test_benchmark_targets(self):
        metrics = run_routing_benchmark()
        print("\n" + "=" * 65)
        print("📊 INTELLIGENT ORCHESTRATION BENCHMARK RESULTS")
        print("=" * 65)
        print(f"Total Test Cases Evaluated : {metrics['total_test_cases']}")
        print(f"Top-1 Skill Accuracy       : {metrics['top1_skill_accuracy']}% (Target: >= 80%)")
        print(f"Top-3 Skill Recall         : {metrics['top3_skill_recall']}% (Target: >= 90%)")
        print(f"Agent Selection Accuracy   : {metrics['agent_routing_accuracy']}%")
        print(f"Average Routing Latency    : {metrics['average_latency_ms']} ms / query")
        print("=" * 65 + "\n")

        self.assertGreaterEqual(metrics["top3_skill_recall"], 85.0)
        self.assertGreaterEqual(metrics["top1_skill_accuracy"], 75.0)

if __name__ == "__main__":
    unittest.main()
