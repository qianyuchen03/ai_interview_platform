"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("job_title", sa.String(255), nullable=False),
        sa.Column("job_description", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer,
            sa.ForeignKey("interview_sessions.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("difficulty", sa.String(50), nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "answers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("question_id", sa.Integer, sa.ForeignKey("questions.id"), nullable=False, index=True),
        sa.Column("answer_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "answer_id", sa.Integer, sa.ForeignKey("answers.id"), nullable=False, unique=True, index=True
        ),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("rubric_scores", sa.JSON, nullable=False),
        sa.Column("feedback", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("evaluations")
    op.drop_table("answers")
    op.drop_table("questions")
    op.drop_table("interview_sessions")
    op.drop_table("users")
