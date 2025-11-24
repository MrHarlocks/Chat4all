from fastapi import APIRouter
from src.api.v1.endpoints import messages, webhooks, files, conversations

api_router = APIRouter()

api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
