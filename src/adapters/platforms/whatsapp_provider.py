from src.domain.interfaces.provider import MessageProvider
from src.domain.models import Message, User
from src.adapters.messaging.kafka_client import get_kafka_producer
from src.core.config import settings
from src.core.logging import logger

class WhatsAppProvider(MessageProvider):
    async def send_message(self, message: Message, to_user: User = None) -> bool:
        try:
            producer = await get_kafka_producer()
            await producer.send_message(
                settings.KAFKA_TOPIC_WHATSAPP_OUT,
                message.model_dump(mode='json')
            )
            logger.info(f"WhatsAppProvider: Enqueued message {message.id} to {settings.KAFKA_TOPIC_WHATSAPP_OUT}")
            return True
        except Exception as e:
            logger.error(f"WhatsAppProvider Error: {e}")
            return False

    async def normalize_payload(self, payload: dict) -> Message:
        # TODO: Implement normalization for WhatsApp payloads
        pass
