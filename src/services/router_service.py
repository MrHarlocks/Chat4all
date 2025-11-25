import json
import asyncio
from src.core.config import settings
from src.core.logging import logger
from src.domain.models import Message, MessageStatus, ConversationType
from src.adapters.messaging.kafka_client import KafkaClient
from src.adapters.db.message_repository import MessageRepository
from src.adapters.db.conversation_repository import ConversationRepository
from src.adapters.platforms.mock_provider import MockProvider
from src.domain.interfaces.provider import MessageProvider

class RouterService:
    def __init__(self):
        self.kafka_client = KafkaClient()
        self.repository = MessageRepository()
        self.conversation_repository = ConversationRepository()
        # In a real app, this would be a factory based on conversation/user settings
        self.providers: dict[str, MessageProvider] = {
            "mock": MockProvider()
        }

    async def start_consumer(self):
        await self.kafka_client.start()
        logger.info(f"RouterService started consuming from {settings.KAFKA_TOPIC_MESSAGES}")
        try:
            async for msg in self.kafka_client.consume(settings.KAFKA_TOPIC_MESSAGES):
                try:
                    data = json.loads(msg.value.decode('utf-8'))
                    message = Message(**data)
                    await self.process_message(message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        finally:
            await self.kafka_client.stop()

    async def process_message(self, message: Message):
        logger.info(f"Routing Message: {message.id} | From: {message.sender_id} | To: {message.conversation_id}")
        
        conversation = await self.conversation_repository.get_by_id(message.conversation_id)
        if conversation and conversation.type == ConversationType.GROUP:
            logger.info(f"Group Fan-out: {conversation.id} | Participants: {len(conversation.participants)}")
            # In a real implementation, we would iterate participants and send to their respective providers.
            # For MVP, we proceed to send to the 'mock' provider which represents the group channel.
        
        # Logic to determine provider (simplified for MVP)
        provider_name = "mock" 
        provider = self.providers.get(provider_name)

        if provider:
            success = await provider.send_message(message)
            new_status = MessageStatus.SENT if success else MessageStatus.FAILED
            await self.repository.update_status(message.id, new_status)
            logger.info(f"Delivery Status: {message.id} -> {new_status} | Provider: {provider_name}")
        else:
            logger.error(f"Delivery Failed: No provider found for message {message.id}")
            await self.repository.update_status(message.id, MessageStatus.FAILED)
