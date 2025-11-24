from fastapi import APIRouter, Request, HTTPException
from src.core.logging import logger

router = APIRouter()

@router.post("/{provider}")
async def webhook_receiver(provider: str, request: Request):
    try:
        payload = await request.json()
        logger.info(f"Received webhook from {provider}: {payload}")
        # TODO: Normalize payload to Message
        # TODO: Push to Inbound Kafka Topic
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
