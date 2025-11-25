from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

class Platform(str, Enum):
    INTERNAL = "INTERNAL"
    WHATSAPP = "WHATSAPP"
    TELEGRAM = "TELEGRAM"
    INSTAGRAM = "INSTAGRAM"

class MessageStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"

class ConversationType(str, Enum):
    PRIVATE = "PRIVATE"
    GROUP = "GROUP"

class MessageType(str, Enum):
    TEXT = "TEXT"
    FILE = "FILE"

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    platform: Platform
    platform_id: str
    display_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FileMetadata(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    mime_type: str
    size: int
    checksum: Optional[str] = None
    uploader_id: UUID
    conversation_id: Optional[UUID] = None
    object_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Attachment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    file_id: Optional[UUID] = None
    url: str
    mime_type: str
    size: int
    filename: str

class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    sender_id: UUID
    type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    attachments: List[Attachment] = []
    status: MessageStatus = MessageStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_metadata: Dict[str, Any] = {}

class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: ConversationType
    participants: List[UUID]
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
