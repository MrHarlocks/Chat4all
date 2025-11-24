import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_get_upload_url():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "filename": "test_image.png",
            "mime_type": "image/png",
            "size": 1024
        }
        
        response = await ac.post("/api/v1/files/upload-url", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "file_id" in data
        assert "public_url" in data
