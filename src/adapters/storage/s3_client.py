import boto3
from botocore.client import Config
from src.core.config import settings

class S3Client:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=settings.S3_REGION
        )

    def generate_presigned_url(self, object_name: str, expiration: int = 3600, method: str = 'put_object'):
        try:
            response = self.client.generate_presigned_url(
                method,
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': object_name
                },
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None

s3_client = S3Client()
