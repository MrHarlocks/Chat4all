from fastapi import APIRouter, Request, HTTPException, Depends
from src.core.logging import logger
from src.services.message_service import MessageService
from src.domain.models import MessageStatus
from uuid import UUID

router = APIRouter()

@router.post("/{provider}", summary="Receber Webhook", description="Endpoint para receber callbacks e mensagens de provedores externos (WhatsApp, Instagram, etc).")
async def webhook_receiver(
    provider: str, 
    request: Request,
    service: MessageService = Depends(MessageService)
):
    """
    Processa webhooks de provedores externos.
    
    - **provider**: Nome do provedor (ex: whatsapp, instagram)
    - **payload**: Corpo da requisição (JSON) contendo eventos ou mensagens
    """
    try:
        payload = await request.json()
        logger.info(f"Received webhook from {provider}: {payload}")
        
        # Check if it's a status update event (from our mocks)
        if payload.get("event") == "status_update":
            message_id = payload.get("message_id")
            status_str = payload.get("status")
            
            if message_id and status_str:
                try:
                    status = MessageStatus(status_str)
                    await service.update_status(UUID(message_id), status)
                    return {"status": "updated"}
                except ValueError:
                    logger.warning(f"Invalid status received: {status_str}")
        
        # TODO: Normalize payload to Message (for inbound messages)
        # TODO: Push to Inbound Kafka Topic
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

