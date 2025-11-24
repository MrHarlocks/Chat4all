from src.domain.models import Conversation, ConversationType
from src.adapters.db.conversation_repository import ConversationRepository
from uuid import uuid4, UUID
from typing import List, Dict, Any
from datetime import datetime, timezone

class ConversationService:
    def __init__(self):
        self.repository = ConversationRepository()

    async def create_conversation(self, type: ConversationType, participants: List[UUID], metadata: Dict[str, Any] = {}) -> Conversation:
        conversation = Conversation(
            id=uuid4(),
            type=type,
            participants=participants,
            metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        await self.repository.create(conversation)
        return conversation

    async def get_conversation(self, conversation_id: UUID) -> Conversation:
        return await self.repository.get_by_id(conversation_id)
