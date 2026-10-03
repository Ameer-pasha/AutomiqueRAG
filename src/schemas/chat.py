from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    document_ids: list[str] | None = None
    stream: bool = False


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int
    chunk_id: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    cached: bool = False
    abstained: bool = False


class FeedbackRequest(BaseModel):
    query: str
    answer: str
    helpful: bool
    note: str | None = None
