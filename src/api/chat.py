from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.dependencies import get_service, get_tenant_id
from src.schemas.chat import ChatRequest, ChatResponse, FeedbackRequest
from src.services import RagService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, tenant_id: str = Depends(get_tenant_id), service: RagService = Depends(get_service)):
    response = await service.answer(request.query, tenant_id, request.document_ids)
    if not request.stream:
        return response
    async def events():
        yield f"event: answer\ndata: {response.model_dump_json()}\n\n"
        yield "event: done\ndata: {}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/feedback", status_code=204)
async def feedback(request: FeedbackRequest, service: RagService = Depends(get_service)):
    service.feedback.append(request.model_dump())
