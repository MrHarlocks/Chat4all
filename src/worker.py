import asyncio
import os
import sys

# Add project root to python path
sys.path.append(os.getcwd())

from src.services.router_service import RouterService
from src.adapters.db.mongo_client import db_client
from src.core.logging import setup_logging, logger

setup_logging()

async def main():
    # Initialize DB connection
    db_client.connect()
    
    # Initialize Router Service
    service = RouterService()
    
    logger.info(f"Starting Router Worker (PID: {os.getpid()})...")
    try:
        await service.start_consumer()
    except Exception as e:
        logger.error(f"Worker failed: {e}")
    finally:
        db_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped manually")
