from src.domain.interfaces.provider import MessageProvider
from src.domain.models import Message, User, Platform, MessageStatus
from uuid import uuid4
from datetime import datetime

class MockProvider(MessageProvider):
    async def send_message(self, message: Message, to_user: User) -> bool:
        print(f"MockProvider: Sending message {message.id} to {to_user.display_name} ({to_user.platform_id})")
        return True

    async def normalize_payload(self, payload: dict) -> Message:
        # Simple mock normalization
        return Message(
            id=uuid4(),
            conversation_id=uuid4(), # In real app, we'd resolve this
            sender_id=uuid4(), # In real app, we'd resolve this
            content=payload.get("text", ""),
            status=MessageStatus.DELIVERED,
            timestamp=datetime.utcnow(),
            provider_metadata=payload
        )
