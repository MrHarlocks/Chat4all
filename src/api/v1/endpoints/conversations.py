from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID
from src.domain.models import Conversation, ConversationType, Message
from src.services.conversation_service import ConversationService

router = APIRouter()

class CreateConversationRequest(BaseModel):
    type: ConversationType
    participants: List[UUID]
    metadata: Dict[str, Any] = {}

@router.post("/", response_model=Conversation, status_code=201)
async def create_conversation(
    request: CreateConversationRequest,
    service: ConversationService = Depends(ConversationService)
):
    try:
        return await service.create_conversation(
            type=request.type,
            participants=request.participants,
            metadata=request.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/messages", response_model=List[Message])
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    service: ConversationService = Depends(ConversationService)
):
    try:
        return await service.get_messages(conversation_id, limit, skip)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
