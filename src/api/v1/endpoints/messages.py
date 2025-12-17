from fastapi import APIRouter, Depends, HTTPException
from src.domain.models import Message, Attachment, MessageType
from src.services.message_service import MessageService
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

router = APIRouter()

class SendMessageRequest(BaseModel):
    conversation_id: UUID
    sender_id: UUID
    type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    file_id: Optional[UUID] = None
    attachments: List[Attachment] = []

@router.post("/", response_model=Message, status_code=201, summary="Enviar mensagem", description="Envia uma nova mensagem para uma conversa específica. Suporta texto e anexos.")
async def send_message(
    request: SendMessageRequest,
    service: MessageService = Depends(MessageService)
):
    """
    Envia uma mensagem para uma conversa.
    
    - **conversation_id**: ID da conversa de destino
    - **sender_id**: ID do remetente
    - **type**: Tipo da mensagem (TEXT, FILE, etc.)
    - **content**: Conteúdo de texto da mensagem (opcional)
    - **file_id**: ID do arquivo anexado (se type=FILE)
    - **attachments**: Lista de anexos adicionais
    """
    try:
        return await service.send_message(
            conversation_id=request.conversation_id,
            sender_id=request.sender_id,
            message_type=request.type,
            content=request.content,
            file_id=request.file_id,
            attachments=request.attachments
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{message_id}", response_model=Message, summary="Obter mensagem", description="Recupera os detalhes de uma mensagem específica pelo seu ID.")
async def get_message(
    message_id: UUID,
    service: MessageService = Depends(MessageService)
):
    """
    Busca uma mensagem pelo ID.
    """
    message = await service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
