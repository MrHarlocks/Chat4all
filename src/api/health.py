from fastapi import APIRouter
from src.adapters.db.mongo_client import db_client

router = APIRouter()

@router.get("/health")
async def health_check():
    # Simple check, maybe check DB connection
    db_status = "connected" if db_client.client else "disconnected"
    return {"status": "ok", "database": db_status}
