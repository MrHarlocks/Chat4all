from fastapi import FastAPI
from src.core.config import settings
from src.core.logging import setup_logging
from src.core.exceptions import add_exception_handlers
from src.core.middleware import LoggingMiddleware
from src.adapters.db.mongo_client import db_client
from src.adapters.messaging.kafka_client import kafka_client
from src.api.v1.router import api_router
from src.api import health
from src.services.router_service import RouterService
from src.core.metrics import MetricsMiddleware
from prometheus_client import make_asgi_app
from fastapi.responses import RedirectResponse
import asyncio

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    API do Roteador Universal de Mensagens
    
    Funcionalidades:
    - Envio e recebimento de mensagens entre plataformas (Interno, WhatsApp, Telegram, etc.)
    - Suporte a transferência de arquivos grandes (até 2GB)
    - Gerenciamento de conversas em grupo
    - Rastreamento de status de mensagens
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Metrics Endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
add_exception_handlers(app)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health.router, tags=["health"])

router_service = RouterService()

@app.on_event("startup")
async def startup_event():
    db_client.connect()
    await kafka_client.start()
    asyncio.create_task(router_service.start_consumer())

@app.on_event("shutdown")
async def shutdown_event():
    db_client.close()
    await kafka_client.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
