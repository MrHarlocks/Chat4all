import asyncio
import httpx
import time
import subprocess
import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from uuid import uuid4
from src.adapters.db.mongo_client import db_client
from src.core.config import settings

import json
from datetime import datetime

# Configuration
API_URL = f"http://localhost:8000{settings.API_V1_STR}"
NUM_MESSAGES = 100
NUM_WORKERS = 2
REPORT_DIR = "tests/reports"

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
    duration = end_time - start_time
    print(f"Sent {success_count}/{count} messages in {duration:.2f}s")
    return success_count, duration

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
    
    # Ensure report directory exists
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "num_messages": NUM_MESSAGES,
            "num_workers": NUM_WORKERS
        },
        "results": {}
    }

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
        sent_count_1, send_time_1 = await send_messages(client, conversation_id, NUM_MESSAGES)
        process_time_1 = await wait_for_processing(conversation_id, NUM_MESSAGES)
        
        report_data["results"]["phase_1"] = {
            "description": "Normal Load",
            "sent_messages": sent_count_1,
            "send_duration_seconds": send_time_1,
            "process_duration_seconds": process_time_1,
            "throughput_mps": NUM_MESSAGES / process_time_1 if process_time_1 else 0
        }

        # Phase 2: Worker Failure
        print("\n--- Phase 2: Simulating Worker Failure ---")
        # Kill one worker
        victim = workers.pop()
        victim.terminate()
        print(f"Killed worker PID: {victim.pid}")
        
        # Send more messages
        sent_count_2, send_time_2 = await send_messages(client, conversation_id, NUM_MESSAGES)
        
        # We expect 2 * NUM_MESSAGES total processed
        process_time_2 = await wait_for_processing(conversation_id, NUM_MESSAGES * 2)
        
        report_data["results"]["phase_2"] = {
            "description": "Worker Failure Recovery",
            "sent_messages": sent_count_2,
            "send_duration_seconds": send_time_2,
            "process_duration_seconds": process_time_2,
            "note": "Processing time includes recovery latency"
        }

    # Cleanup
    print("\nCleaning up...")
    for p in workers:
        p.terminate()
    
    db_client.close()
    
    # Save Report
    report_file = os.path.join(REPORT_DIR, f"scalability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nTest Completed. Report saved to: {report_file}")

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        pass
