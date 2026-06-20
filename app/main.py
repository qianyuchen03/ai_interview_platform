import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import sessions, answers, performance

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI-Powered Interview Prep Platform",
    description=(
        "Generates personalized interview questions from job descriptions and scores "
        "answers with a rubric-based LLM evaluator."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(answers.router, prefix="/api")
app.include_router(performance.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    # Convenience for local/demo use. In a real deployment, run `alembic upgrade head`
    # instead and remove this so schema changes always go through migrations.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve the static frontend (index.html / app.js / styles.css) at the root path.
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
