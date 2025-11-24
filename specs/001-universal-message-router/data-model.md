# Data Model: Universal Message Router

## Entities

### User

Represents a participant in the system. Can be an internal user or an external contact.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `platform` | Enum | `INTERNAL`, `WHATSAPP`, `TELEGRAM`, `INSTAGRAM` |
| `platform_id` | String | ID on the external platform (e.g., phone number, username) |
| `display_name` | String | User's visible name |
| `created_at` | Timestamp | Registration time |

### Conversation

A context for messages. Can be a direct chat or a group.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `type` | Enum | `PRIVATE`, `GROUP` |
| `participants` | List[UUID] | List of User IDs involved |
| `metadata` | Object | Group name, avatar, etc. |
| `created_at` | Timestamp | Creation time |

### Message

The core unit of communication.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `conversation_id` | UUID | Reference to Conversation |
| `sender_id` | UUID | Reference to User |
| `content` | String | Text content (optional if attachment exists) |
| `attachments` | List[Attachment] | List of file attachments |
| `status` | Enum | `PENDING`, `SENT`, `DELIVERED`, `READ`, `FAILED` |
| `timestamp` | Timestamp | When the message was created |
| `provider_metadata` | Object | Raw payload/ID from external provider |

### Attachment

Metadata for a file associated with a message.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `url` | String | S3/MinIO URL for download |
| `mime_type` | String | File type (e.g., `image/jpeg`, `video/mp4`) |
| `size` | Long | Size in bytes |
| `filename` | String | Original filename |

## Storage Schema (MongoDB)

```json
// Collection: messages
{
  "_id": "uuid-v4",
  "conversation_id": "uuid-v4",
  "sender_id": "uuid-v4",
  "content": "Hello world",
  "attachments": [
    {
      "id": "uuid-v4",
      "url": "s3://bucket/path/file.mp4",
      "mime_type": "video/mp4",
      "size": 2147483648
    }
  ],
  "status": "DELIVERED",
  "created_at": "2025-11-23T10:00:00Z",
  "provider_metadata": {
    "telegram_message_id": 12345
  }
}
```

```json
// Collection: conversations
{
  "_id": "uuid-v4",
  "type": "GROUP",
  "participants": ["user-uuid-1", "user-uuid-2"],
  "metadata": {
    "name": "Project Alpha"
  }
}
```
