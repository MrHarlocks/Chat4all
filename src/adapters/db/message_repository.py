from src.adapters.db.mongo_client import get_database
from src.domain.models import Message
from uuid import UUID

class MessageRepository:
    def __init__(self):
        self.collection_name = "messages"

    async def create(self, message: Message) -> Message:
        db = await get_database()
        message_dict = message.model_dump(mode='json')
        # Convert UUIDs to strings for Mongo if needed, but pydantic model_dump(mode='json') handles it mostly.
        # However, we might want to store UUIDs as strings or Binary. Let's stick to strings for simplicity in MVP.
        message_dict['_id'] = str(message.id)
        await db[self.collection_name].insert_one(message_dict)
        return message

    async def get_by_id(self, message_id: UUID) -> Message | None:
        db = await get_database()
        doc = await db[self.collection_name].find_one({"_id": str(message_id)})
        if doc:
            return Message(**doc)
        return None

    async def update_status(self, message_id: UUID, status: str):
        db = await get_database()
        await db[self.collection_name].update_one(
            {"_id": str(message_id)},
            {"$set": {"status": status}}
        )
