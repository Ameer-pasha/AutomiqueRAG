from fastapi import Header, HTTPException

from src.config import get_settings
from src.providers.embeddings.local import HashEmbeddingProvider
from src.providers.llm.gateway import LLMGateway
from src.providers.vectorstore.memory_store import MemoryHybridStore
from src.services import RagService

_settings = get_settings()
_service = RagService(_settings, HashEmbeddingProvider(_settings.embedding_dimension), MemoryHybridStore(), LLMGateway(_settings.llm_base_url, _settings.llm_model, _settings.llm_api_key))


def get_service() -> RagService:
    return _service


def get_tenant_id(x_tenant_id: str = Header("default")) -> str:
    if not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID cannot be empty.")
    return x_tenant_id
