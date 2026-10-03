from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    vector_store: str
    embedding_provider: str
