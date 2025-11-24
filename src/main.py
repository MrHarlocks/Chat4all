from fastapi import FastAPI
from src.core.config import settings
from src.core.logging import setup_logging
from src.core.exceptions import add_exception_handlers
from src.core.middleware import LoggingMiddleware
from src.adapters.db.mongo_client import db_client
from src.adapters.messaging.kafka_client import kafka_client
from src.api.v1.router import api_router
from src.api import health

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    Universal Message Router API
    
    Features:
    - Send and receive messages across platforms (Internal, WhatsApp, Telegram, etc.)
    - Large file transfer support (up to 2GB)
    - Group conversation management
    - Message status tracking
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(LoggingMiddleware)
add_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health.router, tags=["health"])

@app.on_event("startup")
async def startup_event():
    db_client.connect()
    await kafka_client.start()

@app.on_event("shutdown")
async def shutdown_event():
    db_client.close()
    await kafka_client.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
