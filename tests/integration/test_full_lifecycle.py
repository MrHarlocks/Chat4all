import pytest
import httpx
import asyncio
from uuid import uuid4
from src.core.config import settings

# Base URL for the API
BASE_URL = f"http://localhost:8000{settings.API_V1_STR}"

@pytest.mark.asyncio
async def test_full_lifecycle_with_file():
    """
    Test the full lifecycle:
    1. Upload a file
    2. Create a conversation
    3. Send a message with the file attachment
    4. Verify message is created
    5. (Manual verification required for Mock Connector status updates as they are async)
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Upload File
        # ---------------------------------------------------------
        uploader_id = str(uuid4())
        file_payload = {
            "filename": "test_image.png",
            "mime_type": "image/png",
            "size": 1024,
            "uploader_id": uploader_id
        }
        
        response = await client.post("/files/upload-url", json=file_payload)
        assert response.status_code == 200
        file_data = response.json()
        file_id = file_data["file_id"]
        upload_url = file_data["upload_url"]
        
        print(f"\n[1] File Upload URL Generated: {file_id}")

        # Simulate actual upload to MinIO (Optional, but good for completeness)
        # For this test, we just assume the metadata is there, which is enough for the API check.

        # 2. Create Conversation
        # ---------------------------------------------------------
        conv_payload = {
            "type": "PRIVATE",
            "participants": [uploader_id, str(uuid4())],
            "metadata": {"test": "integration"}
        }
        response = await client.post("/conversations/", json=conv_payload)
        assert response.status_code == 201
        conversation_id = response.json()["id"]
        print(f"[2] Conversation Created: {conversation_id}")

        # 3. Send Message with File
        # ---------------------------------------------------------
        msg_payload = {
            "conversation_id": conversation_id,
            "type": "FILE",
            "content": "Here is the image",
            "file_id": file_id
        }
        
        response = await client.post("/messages/", json=msg_payload)
        assert response.status_code == 201
        message_data = response.json()
        message_id = message_data["id"]
        
        assert message_data["type"] == "FILE"
        assert len(message_data["attachments"]) == 1
        assert message_data["attachments"][0]["file_id"] == file_id
        assert message_data["status"] == "PENDING"
        
        print(f"[3] Message Sent: {message_id} | Status: PENDING")

        # 4. Verify Download URL
        # ---------------------------------------------------------
        response = await client.get(f"/files/{file_id}/download-url")
        assert response.status_code == 200
        download_url = response.json()["download_url"]
        assert "http" in download_url
        print(f"[4] Download URL Verified")

        # 5. Wait for Status Updates (Requires Mock Connectors running)
        # ---------------------------------------------------------
        print("[5] Waiting for Mock Connector updates (5s)...")
        await asyncio.sleep(5)
        
        response = await client.get(f"/messages/{message_id}")
        assert response.status_code == 200
        updated_message = response.json()
        
        print(f"[5] Final Message Status: {updated_message['status']}")
        
        # Note: If mocks are not running, this will remain PENDING or SENT.
        # If mocks are running, it should be READ or DELIVERED.
