from src.domain.models import Message, MessageStatus, Attachment, MessageType
from src.adapters.db.message_repository import MessageRepository
from src.adapters.db.file_repository import FileRepository
from src.adapters.messaging.kafka_client import KafkaClient, get_kafka_producer
from src.core.config import settings
from src.core.logging import logger
from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import List, Optional

class MessageService:
    def __init__(self):
        self.repository = MessageRepository()
        self.file_repository = FileRepository()

    async def send_message(
        self, 
        conversation_id: UUID, 
        message_type: MessageType = MessageType.TEXT,
        content: Optional[str] = None, 
        file_id: Optional[UUID] = None,
        attachments: List[Attachment] = []
    ) -> Message:
        
        final_attachments = list(attachments)

        # Validate File if type is FILE
        if message_type == MessageType.FILE:
            if not file_id:
                raise ValueError("file_id is required for messages of type FILE")
            
            file_metadata = await self.file_repository.get_by_id(file_id)
            if not file_metadata:
                raise ValueError(f"File with id {file_id} not found")
            
            # Create attachment from file metadata
            # In a real scenario, we might want to generate a public URL or a temporary download URL here
            # For now, we'll construct the URL based on the object name (or use a placeholder)
            public_url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{file_metadata.object_name}"
            
            attachment = Attachment(
                id=uuid4(),
                file_id=file_metadata.id,
                url=public_url,
                mime_type=file_metadata.mime_type,
                size=file_metadata.size,
                filename=file_metadata.filename
            )
            final_attachments.append(attachment)

        # 1. Create Message Entity
        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            sender_id=uuid4(), # TODO: Get from auth context
            type=message_type,
            content=content,
            attachments=final_attachments,
            status=MessageStatus.PENDING,
            timestamp=datetime.now(timezone.utc)
        )

        logger.info(f"New Message: [User {message.sender_id}] -> [Conv {conversation_id}] | Type: {message_type} | Content: {content[:50] if content else 'No Content'}...")

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

    async def update_status(self, message_id: UUID, status: MessageStatus):
        await self.repository.update_status(message_id, status)
        logger.info(f"Message {message_id} status updated to {status}")

