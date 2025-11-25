from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Universal Message Router"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB
    MONGO_URI: str = "mongodb://admin:password@localhost:27017"
    MONGO_DB_NAME: str = "chat4all"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_MESSAGES: str = "messages"
    KAFKA_TOPIC_STATUS: str = "message_status"
    KAFKA_TOPIC_WHATSAPP_OUT: str = "whatsapp.outbound"
    KAFKA_TOPIC_INSTAGRAM_OUT: str = "instagram.outbound"
    
    # S3/MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "chat-files"
    S3_REGION: str = "us-east-1"
    
    # Security
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
