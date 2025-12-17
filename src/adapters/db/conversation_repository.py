from src.adapters.db.mongo_client import get_database
from src.domain.models import Conversation
from uuid import UUID

class ConversationRepository:
    def __init__(self):
        self.collection_name = "conversations"

    async def create(self, conversation: Conversation):
        db = await get_database()
        data = conversation.model_dump(mode='json')
        data['_id'] = str(conversation.id)
        await db[self.collection_name].insert_one(data)
        return conversation

    async def get_by_id(self, conversation_id: UUID) -> Conversation:
        db = await get_database()
        data = await db[self.collection_name].find_one({"_id": str(conversation_id)})
        if data:
            return Conversation(**data)
        return None

    async def get_by_participant(self, user_id: UUID) -> list[Conversation]:
        db = await get_database()
        cursor = db[self.collection_name].find({"participants": str(user_id)})
        conversations = []
        async for doc in cursor:
            conversations.append(Conversation(**doc))
        return conversations
