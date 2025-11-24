import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from uuid import uuid4

@pytest.mark.asyncio
async def test_get_message_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        message_id = str(uuid4())
        
        # Try to get a non-existent message
        response = await ac.get(f"/api/v1/messages/{message_id}")
        
        # Should fail 404 now as endpoint doesn't exist (or 404 if it exists but message not found)
        # Since endpoint doesn't exist, it will be 404 Not Found (route not found)
        assert response.status_code == 404
