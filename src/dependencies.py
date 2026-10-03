from fastapi import Header, HTTPException

from src.config import get_settings
from src.db.repository import DocumentRepository
from src.providers.embeddings.local import HashEmbeddingProvider
from src.providers.embeddings.ollama import OllamaEmbeddingProvider
from src.providers.llm.gateway import LLMGateway
from src.providers.vectorstore.sqlite_store import SQLiteHybridStore
from src.services import RagService

_settings = get_settings()
_embedder = OllamaEmbeddingProvider(_settings.ollama_base_url, _settings.embedding_model) if _settings.embedding_provider == "ollama" and _settings.embedding_model else HashEmbeddingProvider(_settings.embedding_dimension)
_service = RagService(_settings, _embedder, SQLiteHybridStore(_settings.database_path), LLMGateway(_settings.llm_base_url, _settings.llm_model, _settings.llm_api_key, _settings.llm_max_tokens, _settings.llm_timeout_seconds), DocumentRepository(_settings.database_path))


def get_service() -> RagService:
    return _service


def get_tenant_id(x_tenant_id: str = Header("default")) -> str:
    if not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID cannot be empty.")
    return x_tenant_id
