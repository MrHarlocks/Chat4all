import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_group_conversation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        
        payload = {
            "type": "GROUP",
            "participants": [user1_id, user2_id],
            "metadata": {"name": "Test Group"}
        }
        
        response = await ac.post("/api/v1/conversations/", json=payload)
        
        # Should succeed with 201 Created
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "GROUP"
        assert len(data["participants"]) == 2
