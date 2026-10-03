from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Automique RAG"
    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/files")
    max_upload_mb: int = 50
    embedding_dimension: int = 256
    chunk_size_words: int = 380
    chunk_overlap_words: int = 60
    retrieval_candidates: int = 30
    final_context_chunks: int = 6
    llm_context_chunks: int = 3
    llm_max_tokens: int = 350
    llm_timeout_seconds: int = 120
    relevance_threshold: float = 0.12
    semantic_cache_threshold: float = 0.95
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    embedding_provider: str = "hash"
    embedding_model: str | None = None
    redis_url: str | None = None
    qdrant_url: str | None = None
    database_url: str | None = None
    database_path: Path = Path("data/rag.db")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
