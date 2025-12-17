from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID
from src.domain.models import Conversation, ConversationType, Message
from src.services.conversation_service import ConversationService
from src.services.user_service import UserService

router = APIRouter()

class CreateConversationRequest(BaseModel):
    type: ConversationType
    participants: List[UUID] = []
    participant_names: List[str] = []
    metadata: Dict[str, Any] = {}

@router.post("/", response_model=Conversation, status_code=201, summary="Criar conversa", description="Cria uma nova conversa (individual ou grupo).")
async def create_conversation(
    request: CreateConversationRequest,
    service: ConversationService = Depends(ConversationService),
    user_service: UserService = Depends(UserService)
):
    """
    Inicia uma nova conversa.
    
    - **type**: Tipo da conversa (INDIVIDUAL ou GROUP)
    - **participants**: Lista de IDs dos participantes
    - **participant_names**: Lista de nomes dos participantes (alternativa aos IDs)
    - **metadata**: Metadados adicionais da conversa
    """
    try:
        final_participants = set(request.participants)
        
        # Resolve names to IDs
        for name in request.participant_names:
            user = await user_service.get_by_name(name)
            if not user:
                # Auto-create user if not exists (optional feature for ease of use)
                # Or raise error. Let's raise error to be strict as per "busca o id no banco"
                raise HTTPException(status_code=404, detail=f"Usuário '{name}' não encontrado.")
            final_participants.add(user.id)

        if not final_participants:
            raise HTTPException(status_code=400, detail="É necessário fornecer pelo menos um participante (ID ou Nome).")

        return await service.create_conversation(
            type=request.type,
            participants=list(final_participants),
            metadata=request.metadata
        )
    except HTTPException as he:
        raise he
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

@router.get("/user/{user_id}", response_model=List[Dict[str, Any]], summary="Listar conversas do usuário")
async def list_user_conversations(
    user_id: UUID,
    service: ConversationService = Depends(ConversationService),
    user_service: UserService = Depends(UserService)
):
    """
    Lista todas as conversas onde o usuário é participante, incluindo nomes dos participantes.
    """
    try:
        conversations = await service.list_user_conversations(user_id)
        result = []
        for conv in conversations:
            conv_dict = conv.model_dump()
            # Enrich with participant names
            participant_names = []
            for pid in conv.participants:
                user = await user_service.get_or_create_user(user_id=pid)
                if user:
                    participant_names.append(user.display_name)
            conv_dict['participant_names'] = participant_names
            result.append(conv_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
