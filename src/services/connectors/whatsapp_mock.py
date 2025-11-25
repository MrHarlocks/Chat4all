import asyncio
import json
import httpx
from src.adapters.messaging.kafka_client import KafkaClient
from src.core.config import settings
from src.core.logging import logger
from src.domain.models import Message, MessageStatus

class WhatsAppMockConnector:
    def __init__(self):
        self.kafka_client = KafkaClient()
        self.api_url = f"http://localhost:8000{settings.API_V1_STR}" # Assuming API is running locally

    async def start(self):
        await self.kafka_client.start()
        logger.info(f"WhatsAppMockConnector started consuming from {settings.KAFKA_TOPIC_WHATSAPP_OUT}")
        try:
            async for msg in self.kafka_client.consume(settings.KAFKA_TOPIC_WHATSAPP_OUT):
                try:
                    data = json.loads(msg.value.decode('utf-8'))
                    message = Message(**data)
                    await self.process_message(message)
                except Exception as e:
                    logger.error(f"WhatsAppMockConnector Error: {e}")
        finally:
            await self.kafka_client.stop()

    async def process_message(self, message: Message):
        logger.info(f"[WhatsApp Mock] Received Message: {message.id} | Content: {message.content}")
        
        # Simulate Network Latency
        await asyncio.sleep(2)
        
        # Simulate DELIVERED
        await self.send_status_update(message.id, MessageStatus.DELIVERED)
        logger.info(f"[WhatsApp Mock] Message {message.id} DELIVERED")

        # Simulate User Reading (Wait a bit more)
        await asyncio.sleep(3)
        
        # Simulate READ
        await self.send_status_update(message.id, MessageStatus.READ)
        logger.info(f"[WhatsApp Mock] Message {message.id} READ")

    async def send_status_update(self, message_id, status):
        # In a real scenario, this would be a webhook callback from WhatsApp to our API
        # Here we simulate that callback by calling our own API endpoint
        # We need to implement a callback endpoint in the API first!
        # For now, let's assume there is a generic webhook endpoint or we can use the status update logic directly if we were in the same process.
        # But since this is a "connector", it should act like an external entity calling back.
        
        # Let's use the existing webhook endpoint structure or create a new one.
        # POST /webhooks/whatsapp
        
        payload = {
            "event": "status_update",
            "message_id": str(message_id),
            "status": status.value,
            "timestamp": str(asyncio.get_event_loop().time())
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # We'll use the generic webhook endpoint we have
                await client.post(f"{self.api_url}/webhooks/whatsapp", json=payload)
            except Exception as e:
                logger.error(f"Failed to send callback: {e}")

if __name__ == "__main__":
    connector = WhatsAppMockConnector()
    asyncio.run(connector.start())
