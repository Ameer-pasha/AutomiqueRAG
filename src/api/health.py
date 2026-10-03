from fastapi import APIRouter

from src.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", vector_store="memory-hybrid", embedding_provider="hash-local")
