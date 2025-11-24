import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_send_message_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create a conversation (mocked or real)
        # For MVP US1, we might just send to a conversation ID directly if we assume it exists
        # But let's try to hit the endpoint
        
        payload = {
            "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
            "content": "Hello World",
            "attachments": []
        }
        
        response = await ac.post("/api/v1/messages/", json=payload)
        
        # Should succeed with 201 Created
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PENDING"
        assert "id" in data