from fastapi import APIRouter, Depends

from src.dependencies import get_service
from src.schemas.common import HealthResponse
from src.services import RagService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(service: RagService = Depends(get_service)) -> HealthResponse:
    return HealthResponse(status="ok", vector_store="sqlite-hybrid", embedding_provider=type(service.embedder).__name__)
