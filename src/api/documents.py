import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.config import get_settings
from src.core.ingestion.validator import validate_pdf
from src.dependencies import get_service, get_tenant_id
from src.schemas.document import DocumentResponse
from src.services import RagService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=202)
async def upload_document(file: UploadFile = File(...), tenant_id: str = Depends(get_tenant_id), service: RagService = Depends(get_service)):
    settings = get_settings()
    await validate_pdf(file, settings.max_upload_mb)
    document = service.create_document(file.filename, tenant_id)
    destination = settings.upload_dir / tenant_id / f"{document.id}.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    service.enqueue_ingestion(document.id, destination)
    return document


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, tenant_id: str = Depends(get_tenant_id), service: RagService = Depends(get_service)):
    document = service.documents.get(document_id)
    if not document or document.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, tenant_id: str = Depends(get_tenant_id), service: RagService = Depends(get_service)):
    document = service.documents.get(document_id)
    if not document or document.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    service.store.delete_document(document_id, tenant_id)
    service.documents.pop(document_id)
    Path(get_settings().upload_dir / tenant_id / f"{document_id}.pdf").unlink(missing_ok=True)
