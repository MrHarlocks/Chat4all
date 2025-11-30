import json
import asyncio
from src.core.config import settings
from src.core.logging import logger
from src.domain.models import Message, MessageStatus, ConversationType
from src.adapters.messaging.kafka_client import KafkaClient
from src.adapters.db.message_repository import MessageRepository
from src.adapters.db.conversation_repository import ConversationRepository
from src.adapters.platforms.mock_provider import MockProvider
from src.adapters.platforms.whatsapp_provider import WhatsAppProvider
from src.adapters.platforms.instagram_provider import InstagramProvider
from src.domain.interfaces.provider import MessageProvider
from src.domain.models import Platform
from src.core.metrics import MESSAGES_PROCESSED_TOTAL, ERRORS_TOTAL

class RouterService:
    def __init__(self):
        self.kafka_client = KafkaClient()
        self.repository = MessageRepository()
        self.conversation_repository = ConversationRepository()
        
        self.providers: dict[str, MessageProvider] = {
            Platform.INTERNAL.value: MockProvider(), # Internal/Mock
            Platform.WHATSAPP.value: WhatsAppProvider(),
            Platform.INSTAGRAM.value: InstagramProvider(),
            Platform.TELEGRAM.value: MockProvider(), # Fallback to mock for now
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
                    ERRORS_TOTAL.labels(type="kafka_processing_error").inc()
        finally:
            await self.kafka_client.stop()

    async def process_message(self, message: Message):
        logger.info(f"Routing Message: {message.id} | From: {message.sender_id} | To: {message.conversation_id}")
        
        conversation = await self.conversation_repository.get_by_id(message.conversation_id)
        if not conversation:
            logger.error(f"Conversation {message.conversation_id} not found")
            ERRORS_TOTAL.labels(type="conversation_not_found").inc()
            return

        # Determine recipients (excluding sender)
        # For MVP, we assume 1-1 or Group.
        # We need to find the platform of the recipient(s).
        # Since we don't have a full User Repository in this snippet to look up participants,
        # we will simulate routing based on a hypothetical user lookup or just default to Mock/WhatsApp for testing.
        
        # TODO: Real implementation would look up users. 
        # For now, let's assume if conversation type is PRIVATE, we route to the "other" participant.
        # If we don't have user data, we'll default to WHATSAPP for demonstration if not INTERNAL.
        
        # SIMULATION: Pick a provider based on some logic or random for demo
        # In a real app, we'd do: user = user_repo.get(recipient_id); provider = providers[user.platform]
        
        target_platform = Platform.WHATSAPP.value # Defaulting to WhatsApp for demo purposes of the connector
        
        provider = self.providers.get(target_platform)

        if provider:
            success = await provider.send_message(message)
            # Note: Status update to SENT happens here, but DELIVERED/READ comes from callbacks later
            new_status = MessageStatus.SENT if success else MessageStatus.FAILED
            await self.repository.update_status(message.id, new_status)
            logger.info(f"Delivery Status: {message.id} -> {new_status} | Provider: {target_platform}")
            
            # Metrics
            status_label = "success" if success else "failed"
            MESSAGES_PROCESSED_TOTAL.labels(status=status_label, type=message.type.value).inc()
        else:
            logger.error(f"Delivery Failed: No provider found for platform {target_platform}")
            await self.repository.update_status(message.id, MessageStatus.FAILED)
            MESSAGES_PROCESSED_TOTAL.labels(status="failed", type=message.type.value).inc()
            ERRORS_TOTAL.labels(type="provider_not_found").inc()
