from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(tags=["performance"])


@router.get("/users/{email}/performance", response_model=schemas.PerformanceSummary)
def user_performance(email: str, db: DBSession = Depends(get_db)):
    """Return score trends across sessions and rubric-category breakdown for a user."""
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_performance(db, user)
