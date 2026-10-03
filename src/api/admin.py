from fastapi import APIRouter, Depends

from src.dependencies import get_service
from src.services import RagService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def stats(service: RagService = Depends(get_service)):
    return {"documents": len(service.documents), "feedback": len(service.feedback)}
