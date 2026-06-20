from typing import List, Optional

from sqlalchemy.orm import Session as DBSession

from app import models


def get_or_create_user(db: DBSession, email: str, name: Optional[str] = None) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        if name and not user.name:
            user.name = name
            db.commit()
        return user
    user = models.User(email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: DBSession, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_session_with_questions(
    db: DBSession,
    user: models.User,
    job_title: str,
    job_description: str,
    questions: List[dict],
) -> models.InterviewSession:
    session = models.InterviewSession(
        user_id=user.id, job_title=job_title, job_description=job_description
    )
    db.add(session)
    db.flush()

    for idx, q in enumerate(questions):
        db.add(
            models.Question(
                session_id=session.id,
                text=q["text"],
                category=q.get("category"),
                difficulty=q.get("difficulty"),
                order_index=idx,
            )
        )
    db.commit()
    db.refresh(session)
    _ = session.questions  # touch relationship now so it's loaded before the session closes
    return session


def get_session(db: DBSession, session_id: int) -> Optional[models.InterviewSession]:
    session = (
        db.query(models.InterviewSession)
        .filter(models.InterviewSession.id == session_id)
        .first()
    )
    if session:
        _ = session.questions  # touch relationship now so it's loaded before the session closes
    return session


def get_question(db: DBSession, question_id: int) -> Optional[models.Question]:
    return db.query(models.Question).filter(models.Question.id == question_id).first()


def create_answer_with_evaluation(
    db: DBSession, question: models.Question, answer_text: str, evaluation: dict
) -> models.Answer:
    answer = models.Answer(question_id=question.id, answer_text=answer_text)
    db.add(answer)
    db.flush()

    db.add(
        models.Evaluation(
            answer_id=answer.id,
            overall_score=evaluation["overall_score"],
            rubric_scores=evaluation["rubric_scores"],
            feedback=evaluation["feedback"],
        )
    )
    db.commit()
    db.refresh(answer)
    _ = answer.evaluation  # touch relationship now so it's loaded before the session closes
    return answer


def get_user_performance(db: DBSession, user: models.User) -> dict:
    """Aggregate evaluation scores across all of a user's sessions to surface trends."""
    sessions = (
        db.query(models.InterviewSession)
        .filter(models.InterviewSession.user_id == user.id)
        .order_by(models.InterviewSession.created_at)
        .all()
    )

    trend = []
    category_totals: dict = {}
    all_scores: List[float] = []

    for session in sessions:
        session_scores = []
        for question in session.questions:
            for answer in question.answers:
                if answer.evaluation:
                    session_scores.append(answer.evaluation.overall_score)
                    all_scores.append(answer.evaluation.overall_score)
                    for cat, score in answer.evaluation.rubric_scores.items():
                        category_totals.setdefault(cat, []).append(score)
        if session_scores:
            trend.append(
                {
                    "session_id": session.id,
                    "job_title": session.job_title,
                    "date": session.created_at,
                    "average_score": sum(session_scores) / len(session_scores),
                }
            )

    category_breakdown = [
        {"category": cat, "average_score": sum(vals) / len(vals)}
        for cat, vals in category_totals.items()
    ]

    return {
        "overall_average": (sum(all_scores) / len(all_scores)) if all_scores else None,
        "total_sessions": len(sessions),
        "total_answers": len(all_scores),
        "trend": trend,
        "category_breakdown": category_breakdown,
    }
