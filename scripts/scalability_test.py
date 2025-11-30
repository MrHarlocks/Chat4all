import asyncio
import httpx
import time
import subprocess
import sys
import os
from uuid import uuid4
from src.adapters.db.mongo_client import db_client
from src.core.config import settings

# Configuration
API_URL = f"http://localhost:8000{settings.API_V1_STR}"
NUM_MESSAGES = 100
NUM_WORKERS = 2

async def send_messages(client, conversation_id, count):
    tasks = []
    for i in range(count):
        payload = {
            "conversation_id": conversation_id,
            "type": "TEXT",
            "content": f"Load Test Message {i}"
        }
        tasks.append(client.post("/messages/", json=payload))
    
    start_time = time.time()
    responses = await asyncio.gather(*tasks)
    end_time = time.time()
    
    success_count = sum(1 for r in responses if r.status_code == 201)
    print(f"Sent {success_count}/{count} messages in {end_time - start_time:.2f}s")
    return success_count

async def wait_for_processing(conversation_id, expected_count, timeout=30):
    print(f"Waiting for {expected_count} messages to be processed...")
    db = db_client.get_db()
    collection = db["messages"]
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Count messages in this conversation that are NOT PENDING
        # PENDING means accepted by API but not yet processed by Router
        count = await collection.count_documents({
            "conversation_id": conversation_id,
            "status": {"$ne": "PENDING"}
        })
        
        if count >= expected_count:
            duration = time.time() - start_time
            print(f"Processed {count} messages in {duration:.2f}s")
            return duration
        
        await asyncio.sleep(0.5)
    
    print(f"Timeout! Only processed {count}/{expected_count} messages.")
    return None

async def run_test():
    # Ensure DB connection
    db_client.connect()
    
    # Start Workers
    workers = []
    print(f"Starting {NUM_WORKERS} workers...")
    for _ in range(NUM_WORKERS):
        # Use sys.executable to ensure we use the same python interpreter
        p = subprocess.Popen([sys.executable, "src/worker.py"])
        workers.append(p)
    
    # Give workers time to start
    await asyncio.sleep(5)
    
    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
        # Create Conversation
        user_id = str(uuid4())
        conv_resp = await client.post("/conversations/", json={
            "type": "PRIVATE",
            "participants": [user_id, str(uuid4())]
        })
        if conv_resp.status_code != 201:
            print("Failed to create conversation")
            return
        
        conversation_id = conv_resp.json()["id"]
        
        # Phase 1: Normal Load
        print("\n--- Phase 1: Normal Load ---")
        await send_messages(client, conversation_id, NUM_MESSAGES)
        await wait_for_processing(conversation_id, NUM_MESSAGES)
        
        # Phase 2: Worker Failure
        print("\n--- Phase 2: Simulating Worker Failure ---")
        # Kill one worker
        victim = workers.pop()
        victim.terminate()
        print(f"Killed worker PID: {victim.pid}")
        
        # Send more messages
        await send_messages(client, conversation_id, NUM_MESSAGES)
        
        # We expect 2 * NUM_MESSAGES total processed
        await wait_for_processing(conversation_id, NUM_MESSAGES * 2)
        
    # Cleanup
    print("\nCleaning up...")
    for p in workers:
        p.terminate()
    
    db_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        pass
