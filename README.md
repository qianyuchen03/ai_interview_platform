# AI-Powered Interview Prep Platform

An AI-driven interview prep platform that generates personalized interview questions
from a job description and gives candidates rubric-based feedback on their answers,
tracking question history and performance trends across sessions.

**Stack:** Python (FastAPI), OpenAI API, PostgreSQL (SQLAlchemy + Alembic), vanilla JS frontend.

## How it works

1. A candidate submits a job title + job description.
2. The backend calls the OpenAI API (prompt orchestration in `app/services/llm_service.py`)
   to generate a personalized set of behavioral/technical interview questions.
3. The candidate answers each question. Each answer is scored by the LLM against a
   fixed rubric (relevance, structure, specificity, communication), producing a
   per-criterion score, an overall score, and written feedback.
4. Every session, question, answer, and evaluation is persisted in PostgreSQL, so a
   `/performance` endpoint can compute score trends across sessions and a breakdown
   by rubric category.

If the OpenAI call fails for any reason (no key, rate limit, network issue), both the
question generator and the evaluator fall back to deterministic logic so the app keeps
working end to end.

## Project layout

```
app/
  main.py              FastAPI app, CORS, static frontend mount, table creation on startup
  config.py            Settings (env vars / .env)
  database.py          SQLAlchemy engine/session
  models.py            User, InterviewSession, Question, Answer, Evaluation
  schemas.py           Pydantic request/response models
  crud.py              DB read/write + performance aggregation
  services/
    llm_service.py     OpenAI prompt orchestration (question gen + rubric evaluation)
    rubric.py          Shared rubric definition
  routers/
    sessions.py        POST /api/sessions, GET /api/sessions/{id}, GET /api/users/{email}/sessions
    answers.py         POST /api/questions/{id}/answers
    performance.py     GET /api/users/{email}/performance
alembic/               Schema migrations
frontend/              Static single-page UI (index.html / app.js / styles.css)
tests/test_smoke.py    End-to-end smoke test (SQLite + mocked LLM calls)
```

## Data model

- **users** — email, name
- **interview_sessions** — one per job description, belongs to a user
- **questions** — generated per session, with category/difficulty/order
- **answers** — candidate's response to a question
- **evaluations** — one per answer: overall score, JSON rubric score breakdown, feedback

## Setup

### Option A: Docker Compose (recommended, runs Postgres + API together)

```bash
cp .env.example .env        # add your OPENAI_API_KEY
docker compose up --build
```

API: http://localhost:8000/docs · Frontend: http://localhost:8000

### Option B: Local Python + your own Postgres

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

createdb interview_prep      # or create it via psql / a GUI client
cp .env.example .env         # set DATABASE_URL and OPENAI_API_KEY

alembic upgrade head         # creates the schema
uvicorn app.main:app --reload
```

Then open http://localhost:8000 for the UI, or http://localhost:8000/docs for the
interactive API docs.

## API summary

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/sessions` | Create a session; generates personalized questions from a job description |
| GET | `/api/sessions/{id}` | Fetch a session and its questions |
| GET | `/api/users/{email}/sessions` | List a user's sessions |
| POST | `/api/questions/{id}/answers` | Submit an answer; returns the rubric-based evaluation |
| GET | `/api/users/{email}/performance` | Score trend across sessions + rubric-category averages |

## Testing

```bash
pip install -r requirements.txt
pytest
```

`tests/test_smoke.py` runs the full create-session → answer → evaluate → performance
flow against SQLite with the LLM calls mocked, so it doesn't require Postgres or a
live OpenAI key.

## Notes / next steps

- Auth is intentionally left out (sessions are keyed by email) to keep the demo simple;
  swap in real auth (JWT/OAuth) before any production use.
- `app/main.py` calls `Base.metadata.create_all()` on startup for local convenience.
  In a real deployment, drop that and rely solely on `alembic upgrade head`.
- Rubric criteria live in `app/services/rubric.py` — edit them to change what the
  LLM scores answers on.
