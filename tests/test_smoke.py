"""End-to-end smoke test: exercises the full create-session -> answer -> evaluate ->
performance flow against an in-memory SQLite DB with the LLM service mocked out, so
it runs without a real Postgres instance or OpenAI key.
"""

import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["OPENAI_API_KEY"] = "test-key"

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import llm_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def patch_llm(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "generate_questions",
        lambda job_title, job_description, num_questions=5: [
            {"text": f"Sample question {i}", "category": "general", "difficulty": "easy"}
            for i in range(num_questions)
        ],
    )
    monkeypatch.setattr(
        llm_service,
        "evaluate_answer",
        lambda question_text, answer_text: {
            "rubric_scores": {
                "relevance": 4,
                "structure": 3,
                "specificity": 4,
                "communication": 5,
            },
            "overall_score": 8.0,
            "feedback": "Solid answer with a clear example.",
        },
    )


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_full_flow():
    res = client.post(
        "/api/sessions",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "job_title": "Backend Engineer",
            "job_description": "Build APIs with Python and PostgreSQL.",
            "num_questions": 3,
        },
    )
    assert res.status_code == 200
    session = res.json()
    assert len(session["questions"]) == 3

    question_id = session["questions"][0]["id"]
    res = client.post(
        f"/api/questions/{question_id}/answers",
        json={"answer_text": "I built a REST API using FastAPI and PostgreSQL for a prior project."},
    )
    assert res.status_code == 200
    answer = res.json()
    assert answer["evaluation"]["overall_score"] == 8.0

    res = client.get("/api/users/test@example.com/performance")
    assert res.status_code == 200
    perf = res.json()
    assert perf["total_sessions"] == 1
    assert perf["overall_average"] == 8.0
