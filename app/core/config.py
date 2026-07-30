import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kazilen Backend"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-local-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./kazilen.db")

    class Config:
        env_file = ".env"

settings = Settings()
