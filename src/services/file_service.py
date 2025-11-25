from uuid import uuid4, UUID
from typing import Optional
from src.adapters.storage.s3_client import s3_client
from src.core.config import settings
from src.adapters.db.file_repository import FileRepository
from src.domain.models import FileMetadata

class FileService:
    def __init__(self):
        self.s3 = s3_client
        self.repository = FileRepository()

    async def generate_upload_url(
        self, 
        filename: str, 
        mime_type: str, 
        size: int, 
        uploader_id: UUID, 
        conversation_id: Optional[UUID] = None,
        checksum: Optional[str] = None
    ):
        file_id = uuid4()
        extension = filename.split('.')[-1] if '.' in filename else 'bin'
        object_name = f"{file_id}.{extension}"
        
        # Note: generate_presigned_url is synchronous in boto3, but we wrap it in async service method
        # for consistency and potential future async implementation
        upload_url = self.s3.generate_presigned_url(object_name, method='put_object')
        
        # Construct a public URL (assuming bucket policy allows read or using MinIO browser)
        # In production, this might be a CloudFront URL
        public_url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{object_name}"

        # Save metadata
        file_metadata = FileMetadata(
            id=file_id,
            filename=filename,
            mime_type=mime_type,
            size=size,
            uploader_id=uploader_id,
            conversation_id=conversation_id,
            checksum=checksum,
            object_name=object_name
        )
        await self.repository.create(file_metadata)

        return {
            "upload_url": upload_url,
            "file_id": str(file_id),
            "public_url": public_url,
            "object_name": object_name
        }

    async def generate_download_url(self, file_id: UUID) -> Optional[str]:
        file_metadata = await self.repository.get_by_id(file_id)
        if not file_metadata:
            return None
        
        download_url = self.s3.generate_presigned_url(
            file_metadata.object_name, 
            method='get_object'
        )
        return download_url

