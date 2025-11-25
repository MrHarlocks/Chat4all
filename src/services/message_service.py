from src.domain.models import Message, MessageStatus, Attachment
from src.adapters.db.message_repository import MessageRepository
from src.adapters.messaging.kafka_client import KafkaClient, get_kafka_producer
from src.core.config import settings
from src.core.logging import logger
from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import List, Optional

class MessageService:
    def __init__(self):
        self.repository = MessageRepository()

    async def send_message(self, conversation_id: UUID, content: Optional[str] = None, attachments: List[Attachment] = []) -> Message:
        # 1. Create Message Entity
        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            sender_id=uuid4(), # TODO: Get from auth context
            content=content,
            attachments=attachments,
            status=MessageStatus.PENDING,
            timestamp=datetime.now(timezone.utc)
        )

        logger.info(f"New Message: [User {message.sender_id}] -> [Conv {conversation_id}] | Content: {content[:50] if content else 'No Content'}...")

        # 2. Persist to DB
        await self.repository.create(message)

        # 3. Push to Kafka
        kafka = await get_kafka_producer()
        await kafka.send_message(
            settings.KAFKA_TOPIC_MESSAGES,
            message.model_dump(mode='json')
        )

        return message

    async def get_message(self, message_id: UUID) -> Message:
        message = await self.repository.get_by_id(message_id)
        if not message:
            return None
        return message
