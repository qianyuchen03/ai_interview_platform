"""Shared rubric definition used to prompt and parse LLM answer evaluations."""

RUBRIC_CRITERIA = {
    "relevance": "How directly the answer addresses the question and the role's requirements.",
    "structure": "Use of a clear structure (e.g. STAR: Situation, Task, Action, Result).",
    "specificity": "Concrete details, metrics, and examples rather than vague statements.",
    "communication": "Clarity, conciseness, and confidence of the delivery.",
}


def rubric_description() -> str:
    lines = [f"- {name} (1-5): {desc}" for name, desc in RUBRIC_CRITERIA.items()]
    return "\n".join(lines)
