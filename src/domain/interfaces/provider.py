from abc import ABC, abstractmethod
from src.domain.models import Message, User

class MessageProvider(ABC):
    @abstractmethod
    async def send_message(self, message: Message, to_user: User) -> bool:
        """Send a message to a user on this platform."""
        pass

    @abstractmethod
    async def normalize_payload(self, payload: dict) -> Message:
        """Convert external platform payload to internal Message entity."""
        pass
