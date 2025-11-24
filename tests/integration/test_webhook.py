import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_webhook_ingestion():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Simulate a webhook from Telegram
        payload = {
            "update_id": 10000,
            "message": {
                "message_id": 1365,
                "from": {
                    "id": 1111111,
                    "is_bot": False,
                    "first_name": "John"
                },
                "chat": {
                    "id": 1111111,
                    "first_name": "John",
                    "type": "private"
                },
                "date": 1441645532,
                "text": "Hello from Telegram"
            }
        }
        
        response = await ac.post("/api/v1/webhooks/telegram", json=payload)
        
        # Should fail 404
        assert response.status_code == 200
        assert response.json() == {"status": "received"}
