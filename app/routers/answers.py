from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import crud, schemas
from app.database import get_db
from app.services import llm_service

router = APIRouter(tags=["answers"])


@router.post("/questions/{question_id}/answers", response_model=schemas.AnswerOut)
def submit_answer(question_id: int, payload: schemas.AnswerCreate, db: DBSession = Depends(get_db)):
    """Submit an answer to a question; triggers rubric-based LLM evaluation."""
    question = crud.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    evaluation = llm_service.evaluate_answer(question.text, payload.answer_text)
    answer = crud.create_answer_with_evaluation(db, question, payload.answer_text, evaluation)
    return answer
