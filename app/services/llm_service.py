"""LLM prompt orchestration: personalized question generation + rubric-based answer evaluation."""

import json
import logging
from typing import Any, Dict, List

from openai import OpenAI

from app.config import settings
from app.services.rubric import RUBRIC_CRITERIA, rubric_description

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def generate_questions(
    job_title: str, job_description: str, num_questions: int = 5
) -> List[Dict[str, Any]]:
    """Generate personalized interview questions for a job description via the LLM.

    Falls back to a deterministic template set if the API call fails (missing key,
    rate limit, network error, malformed response, etc.) so the app stays usable.
    """
    system_prompt = (
        "You are an experienced technical interviewer. Generate realistic, role-specific "
        "interview questions strictly based on the job title and job description provided. "
        "Mix behavioral and technical questions appropriate to the role. "
        'Respond ONLY with JSON of the form: '
        '{"questions": [{"text": str, "category": str, "difficulty": "easy|medium|hard"}]}'
    )
    user_prompt = (
        f"Job title: {job_title}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Generate exactly {num_questions} interview questions."
    )

    try:
        response = get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        payload = json.loads(response.choices[0].message.content)
        questions = payload.get("questions", [])[:num_questions]
        if not questions:
            raise ValueError("LLM returned no questions")
        return questions
    except Exception:
        logger.exception("LLM question generation failed, falling back to template questions")
        return _fallback_questions(job_title, num_questions)


def evaluate_answer(question_text: str, answer_text: str) -> Dict[str, Any]:
    """Score a candidate's answer against the interview rubric via the LLM.

    Falls back to a heuristic score if the API call fails, so the evaluation
    pipeline never hard-fails even without a working LLM connection.
    """
    system_prompt = (
        "You are a rigorous, fair interview coach. Score the candidate's answer against this "
        f"rubric, each criterion from 1 (poor) to 5 (excellent):\n{rubric_description()}\n\n"
        'Respond ONLY with JSON of the form: {"rubric_scores": {<criterion>: <1-5>, ...}, '
        '"overall_score": <0-10 float>, "feedback": <2-4 sentence actionable feedback>}'
    )
    user_prompt = f"Question: {question_text}\n\nCandidate's answer: {answer_text}"

    try:
        response = get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        payload = json.loads(response.choices[0].message.content)
        rubric_scores = {k: float(v) for k, v in payload["rubric_scores"].items()}
        overall_score = float(payload["overall_score"])
        feedback = payload["feedback"]
        return {
            "rubric_scores": rubric_scores,
            "overall_score": overall_score,
            "feedback": feedback,
        }
    except Exception:
        logger.exception("LLM evaluation failed, falling back to heuristic scoring")
        return _fallback_evaluation(answer_text)


def _fallback_questions(job_title: str, num_questions: int) -> List[Dict[str, Any]]:
    templates = [
        {
            "text": f"Walk me through a project where you applied core skills relevant to a {job_title} role.",
            "category": "experience",
            "difficulty": "medium",
        },
        {
            "text": "Tell me about a time you disagreed with a teammate. How did you resolve it?",
            "category": "behavioral",
            "difficulty": "easy",
        },
        {
            "text": f"What technical challenge do you expect to be hardest in a {job_title} position, and how would you approach it?",
            "category": "technical",
            "difficulty": "hard",
        },
        {
            "text": "Describe a time you had to learn a new tool or technology quickly.",
            "category": "behavioral",
            "difficulty": "easy",
        },
        {
            "text": "How do you prioritize tasks when working on multiple deadlines at once?",
            "category": "behavioral",
            "difficulty": "medium",
        },
    ]
    return templates[:num_questions]


def _fallback_evaluation(answer_text: str) -> Dict[str, Any]:
    length_score = min(5, max(1, len(answer_text.split()) // 20))
    rubric_scores = {name: float(length_score) for name in RUBRIC_CRITERIA}
    overall_score = float(length_score) * 2
    feedback = (
        "Automated scoring unavailable (LLM call failed) — this is a heuristic placeholder "
        "score. Add more specific examples and quantify results for a stronger answer."
    )
    return {"rubric_scores": rubric_scores, "overall_score": overall_score, "feedback": feedback}
