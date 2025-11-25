from src.adapters.db.mongo_client import get_database
from src.domain.models import FileMetadata
from uuid import UUID

class FileRepository:
    def __init__(self):
        self.collection_name = "files"

    async def create(self, file_metadata: FileMetadata) -> FileMetadata:
        db = await get_database()
        file_dict = file_metadata.model_dump(mode='json')
        file_dict['_id'] = str(file_metadata.id)
        await db[self.collection_name].insert_one(file_dict)
        return file_metadata

    async def get_by_id(self, file_id: UUID) -> FileMetadata | None:
        db = await get_database()
        doc = await db[self.collection_name].find_one({"_id": str(file_id)})
        if doc:
            return FileMetadata(**doc)
        return None
