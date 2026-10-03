from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_service, get_tenant_id
from src.schemas.document import DocumentResponse
from src.services import RagService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def stats(service: RagService = Depends(get_service)):
    return {"documents": len(service.documents), "feedback": len(service.feedback)}


@router.post("/reindex/{document_id}", response_model=DocumentResponse, status_code=202)
async def reindex(document_id: str, tenant_id: str = Depends(get_tenant_id), service: RagService = Depends(get_service)):
    document = service.documents.get(document_id)
    if not document or document.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    service.enqueue_reindex(document_id)
    return document
