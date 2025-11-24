# Quickstart: Universal Message Router

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- `curl` or Postman

## Running the Stack

1. **Start Infrastructure** (Kafka, MongoDB, MinIO):

   ```bash
   docker-compose up -d
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API**:

   ```bash
   uvicorn src.main:app --reload
   ```

## Usage Examples

### 1. Create a Conversation

```bash
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "type": "GROUP",
    "participants": ["user-uuid-1", "user-uuid-2"],
    "metadata": {"name": "Test Group"}
  }'
```

### 2. Upload a File (Step 1: Get URL)

```bash
curl -X POST http://localhost:8000/api/v1/files/upload-url \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "mime_type": "video/mp4",
    "size": 10485760
  }'
```

### 3. Send a Message

```bash
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-uuid-from-step-1",
    "content": "Hello from CLI!",
    "attachments": [
        {
            "id": "file-id-from-step-2",
            "url": "http://minio:9000/bucket/file-id.mp4",
            "mime_type": "video/mp4",
            "size": 10485760,
            "filename": "video.mp4"
        }
    ]
  }'
```

## Testing

Run the integration tests (requires Docker):

```bash
pytest tests/integration
```
