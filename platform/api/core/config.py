"""
Configurare centralizată — citită din variabile de mediu / .env
"""
from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Clinică
    CLINIC_ID: str
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "info"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://foreverhuman:password@localhost:5432/foreverhuman"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LanceDB
    LANCEDB_PATH: str = "/data/lancedb"

    # JWT
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # LLM
    LLM_PROVIDER: Literal["anthropic", "gemini", "ollama"] = "gemini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"

    # Embeddings
    EMBEDDING_PROVIDER: Literal["openai", "ollama"] = "openai"
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:19006"]


settings = Settings()
