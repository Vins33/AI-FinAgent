from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str
    CHECKPOINT_PG_DSN: str = ""

    # Ollama LLM
    OLLAMA_BASE_URL: str
    LLM_MODEL_NAME: str = "gpt-oss:20b"
    LLM_TEMPERATURE: float = 0.1
    LLM_KEEP_ALIVE: str = "4h"
    LLM_SEED: int = 42
    LLM_NUM_CTX: int = 16384  # Context window per la memoria conversazione

    # Qdrant Vector Store
    QDRANT_HOST: str
    QDRANT_PORT: int = 6333
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"

    # API Keys
    SERPAPI_API_KEY: str


settings = Settings()
