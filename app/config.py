from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized app configuration, loaded from environment / .env file."""

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/interview_prep"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
