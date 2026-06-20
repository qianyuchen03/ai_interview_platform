from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import crud, schemas
from app.database import get_db
from app.services import llm_service

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=schemas.SessionOut)
def create_session(payload: schemas.SessionCreate, db: DBSession = Depends(get_db)):
    """Create a new interview session and generate personalized questions for it."""
    user = crud.get_or_create_user(db, email=payload.email, name=payload.name)
    questions = llm_service.generate_questions(
        payload.job_title, payload.job_description, payload.num_questions
    )
    session = crud.create_session_with_questions(
        db, user, payload.job_title, payload.job_description, questions
    )
    return session


@router.get("/sessions/{session_id}", response_model=schemas.SessionOut)
def read_session(session_id: int, db: DBSession = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/users/{email}/sessions", response_model=list[schemas.SessionOut])
def list_user_sessions(email: str, db: DBSession = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    sessions = user.sessions
    for s in sessions:
        _ = s.questions  # touch relationship now so it's loaded before the session closes
    return sessions
