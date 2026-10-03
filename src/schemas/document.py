from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DocumentStatus(StrEnum):
    queued = "queued"
    parsing = "parsing"
    chunking = "chunking"
    indexing = "indexing"
    indexed = "indexed"
    failed = "failed"


class DocumentResponse(BaseModel):
    id: str
    filename: str
    tenant_id: str
    status: DocumentStatus
    created_at: datetime
    page_count: int = 0
    chunk_count: int = 0
    error: str | None = None
