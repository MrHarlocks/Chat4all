from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings

class MongoDBClient:
    client: AsyncIOMotorClient = None

    def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        print("Connected to MongoDB")

    def close(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_db(self):
        return self.client[settings.MONGO_DB_NAME]

db_client = MongoDBClient()

async def get_database():
    return db_client.get_db()
