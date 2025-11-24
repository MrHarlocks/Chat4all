from uuid import uuid4
from src.adapters.storage.s3_client import s3_client
from src.core.config import settings

class FileService:
    def __init__(self):
        self.s3 = s3_client

    async def generate_upload_url(self, filename: str, mime_type: str, size: int):
        file_id = uuid4()
        extension = filename.split('.')[-1] if '.' in filename else 'bin'
        object_name = f"{file_id}.{extension}"
        
        # Note: generate_presigned_url is synchronous in boto3, but we wrap it in async service method
        # for consistency and potential future async implementation
        upload_url = self.s3.generate_presigned_url(object_name, method='put_object')
        
        # Construct a public URL (assuming bucket policy allows read or using MinIO browser)
        # In production, this might be a CloudFront URL
        public_url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{object_name}"

        return {
            "upload_url": upload_url,
            "file_id": str(file_id),
            "public_url": public_url,
            "object_name": object_name
        }
