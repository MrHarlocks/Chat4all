from src.adapters.db.mongo_client import get_database
from src.domain.models import User
from uuid import UUID

class UserRepository:
    def __init__(self):
        self.collection_name = "users"

    async def create(self, user: User) -> User:
        db = await get_database()
        data = user.model_dump(mode='json')
        data['_id'] = str(user.id)
        await db[self.collection_name].insert_one(data)
        return user

    async def get_by_id(self, user_id: UUID) -> User:
        db = await get_database()
        data = await db[self.collection_name].find_one({"_id": str(user_id)})
        if data:
            return User(**data)
        return None

    async def get_by_display_name(self, display_name: str) -> User:
        db = await get_database()
        data = await db[self.collection_name].find_one({"display_name": display_name})
        if data:
            return User(**data)
        return None
