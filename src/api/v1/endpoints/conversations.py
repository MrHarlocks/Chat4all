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

@router.post("/", response_model=Conversation, status_code=201, summary="Criar conversa", description="Cria uma nova conversa (individual ou grupo).")
async def create_conversation(
    request: CreateConversationRequest,
    service: ConversationService = Depends(ConversationService)
):
    """
    Inicia uma nova conversa.
    
    - **type**: Tipo da conversa (INDIVIDUAL ou GROUP)
    - **participants**: Lista de IDs dos participantes
    - **metadata**: Metadados adicionais da conversa
    """
    try:
        return await service.create_conversation(
            type=request.type,
            participants=request.participants,
            metadata=request.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/messages", response_model=List[Message], summary="Listar mensagens", description="Recupera o histórico de mensagens de uma conversa com paginação.")
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de mensagens a retornar"),
    skip: int = Query(0, ge=0, description="Número de mensagens a pular (paginação)"),
    service: ConversationService = Depends(ConversationService)
):
    """
    Lista mensagens de uma conversa.
    """
    try:
        return await service.get_messages(conversation_id, limit, skip)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=List[Conversation], summary="Listar conversas do usuário")
async def list_user_conversations(
    user_id: UUID,
    service: ConversationService = Depends(ConversationService)
):
    """
    Lista todas as conversas onde o usuário é participante.
    """
    try:
        return await service.list_user_conversations(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
