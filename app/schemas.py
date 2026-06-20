import datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, EmailStr, Field


class QuestionOut(BaseModel):
    id: int
    text: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    order_index: int

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    job_title: str
    job_description: str
    num_questions: int = Field(default=5, ge=1, le=10)


class SessionOut(BaseModel):
    id: int
    job_title: str
    job_description: str
    created_at: datetime.datetime
    questions: List[QuestionOut]

    class Config:
        from_attributes = True


class AnswerCreate(BaseModel):
    answer_text: str


class EvaluationOut(BaseModel):
    overall_score: float
    rubric_scores: Dict[str, float]
    feedback: str

    class Config:
        from_attributes = True


class AnswerOut(BaseModel):
    id: int
    question_id: int
    answer_text: str
    evaluation: Optional[EvaluationOut] = None

    class Config:
        from_attributes = True


class SessionTrendPoint(BaseModel):
    session_id: int
    job_title: str
    date: datetime.datetime
    average_score: float


class CategoryAverage(BaseModel):
    category: str
    average_score: float


class PerformanceSummary(BaseModel):
    overall_average: Optional[float] = None
    total_sessions: int
    total_answers: int
    trend: List[SessionTrendPoint]
    category_breakdown: List[CategoryAverage]
