import asyncio
import json
import httpx
from src.adapters.messaging.kafka_client import KafkaClient
from src.core.config import settings
from src.core.logging import logger
from src.domain.models import Message, MessageStatus

class InstagramMockConnector:
    def __init__(self):
        self.kafka_client = KafkaClient()
        self.api_url = f"http://localhost:8000{settings.API_V1_STR}"

    async def start(self):
        await self.kafka_client.start()
        logger.info(f"InstagramMockConnector started consuming from {settings.KAFKA_TOPIC_INSTAGRAM_OUT}")
        try:
            async for msg in self.kafka_client.consume(settings.KAFKA_TOPIC_INSTAGRAM_OUT):
                try:
                    data = json.loads(msg.value.decode('utf-8'))
                    message = Message(**data)
                    await self.process_message(message)
                except Exception as e:
                    logger.error(f"InstagramMockConnector Error: {e}")
        finally:
            await self.kafka_client.stop()

    async def process_message(self, message: Message):
        logger.info(f"[Instagram Mock] Received Message: {message.id} | Content: {message.content}")
        
        # Simulate Network Latency
        await asyncio.sleep(1)
        
        # Simulate DELIVERED
        await self.send_status_update(message.id, MessageStatus.DELIVERED)
        logger.info(f"[Instagram Mock] Message {message.id} DELIVERED")

        # Simulate READ
        await asyncio.sleep(2)
        await self.send_status_update(message.id, MessageStatus.READ)
        logger.info(f"[Instagram Mock] Message {message.id} READ")

    async def send_status_update(self, message_id, status):
        payload = {
            "event": "status_update",
            "message_id": str(message_id),
            "status": status.value
        }
        
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{self.api_url}/webhooks/instagram", json=payload)
            except Exception as e:
                logger.error(f"Failed to send callback: {e}")

if __name__ == "__main__":
    connector = InstagramMockConnector()
    asyncio.run(connector.start())
