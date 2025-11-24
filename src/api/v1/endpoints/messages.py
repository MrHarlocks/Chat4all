from fastapi import APIRouter, Depends, HTTPException
from src.domain.models import Message, Attachment
from src.services.message_service import MessageService
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

router = APIRouter()

class SendMessageRequest(BaseModel):
    conversation_id: UUID
    content: Optional[str] = None
    attachments: List[Attachment] = []

@router.post("/", response_model=Message, status_code=201)
async def send_message(
    request: SendMessageRequest,
    service: MessageService = Depends(MessageService)
):
    try:
        return await service.send_message(
            conversation_id=request.conversation_id,
            content=request.content,
            attachments=request.attachments
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{message_id}", response_model=Message)
async def get_message(
    message_id: UUID,
    service: MessageService = Depends(MessageService)
):
    message = await service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
