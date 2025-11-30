import asyncio
import httpx
import time
import subprocess
import sys
import os
from datetime import datetime
from uuid import uuid4
from src.adapters.db.mongo_client import db_client
from src.core.config import settings

# Configuration
API_URL = f"http://localhost:8000{settings.API_V1_STR}"
REPORT_FILE = "tests/reports/fault_tolerance_report.md"
NUM_WORKERS = 2
MESSAGES_BATCH_1 = 100
MESSAGES_BATCH_2 = 50

class FaultToleranceTester:
    def __init__(self):
        self.report_lines = []
        self.workers = []
        self.conversation_id = None
        self.client = None

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        self.report_lines.append(f"- {line}")

    def add_section(self, title):
        print(f"\n=== {title} ===")
        self.report_lines.append(f"\n### {title}")

    async def setup(self):
        self.add_section("Setup Environment")
        db_client.connect()
        
        # Start Workers
        self.log(f"Starting {NUM_WORKERS} workers...")
        for i in range(NUM_WORKERS):
            p = subprocess.Popen([sys.executable, "src/worker.py"])
            self.workers.append(p)
            self.log(f"Started Worker {i+1} (PID: {p.pid})")
        
        # Wait for startup
        await asyncio.sleep(5)
        
        self.client = httpx.AsyncClient(base_url=API_URL, timeout=30.0)
        
        # Create Conversation
        user_id = str(uuid4())
        resp = await self.client.post("/conversations/", json={
            "type": "PRIVATE",
            "participants": [user_id, str(uuid4())]
        })
        self.conversation_id = resp.json()["id"]
        self.log(f"Created Test Conversation: {self.conversation_id}")

    async def send_batch(self, count, prefix="Msg"):
        self.log(f"Sending batch of {count} messages...")
        tasks = []
        for i in range(count):
            payload = {
                "conversation_id": self.conversation_id,
                "type": "TEXT",
                "content": f"{prefix} {i}"
            }
            tasks.append(self.client.post("/messages/", json=payload))
        
        start = time.time()
        responses = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        success = sum(1 for r in responses if r.status_code == 201)
        self.log(f"Sent {success}/{count} messages in {duration:.2f}s")
        return success

    async def wait_for_processing(self, total_expected, timeout=60):
        self.log(f"Waiting for {total_expected} messages to be processed...")
        db = db_client.get_db()
        collection = db["messages"]
        
        start = time.time()
        while time.time() - start < timeout:
            count = await collection.count_documents({
                "conversation_id": self.conversation_id,
                "status": {"$ne": "PENDING"}
            })
            
            if count >= total_expected:
                duration = time.time() - start
                self.log(f"SUCCESS: Processed {count} messages in {duration:.2f}s")
                return True
            
            await asyncio.sleep(1)
            
        self.log(f"TIMEOUT: Only processed {count}/{total_expected} messages")
        return False

    async def run(self):
        try:
            await self.setup()

            # --- Scenario 1: Kill Worker during Load ---
            self.add_section("Scenario 1: Worker Failure under Load")
            
            # Send messages
            send_task = asyncio.create_task(self.send_batch(MESSAGES_BATCH_1, "Batch1"))
            
            # Wait a bit then kill a worker
            await asyncio.sleep(1)
            victim = self.workers.pop()
            victim.terminate()
            self.log(f"⚠️ KILLED Worker (PID: {victim.pid}) while processing")
            
            await send_task
            
            # Verify all processed
            success = await self.wait_for_processing(MESSAGES_BATCH_1)
            if success:
                self.log("✅ System recovered and processed all messages.")
            else:
                self.log("❌ Message loss detected.")

            # --- Scenario 2: Recovery & Redistribution ---
            self.add_section("Scenario 2: Service Recovery")
            
            # Restart worker
            new_worker = subprocess.Popen([sys.executable, "src/worker.py"])
            self.workers.append(new_worker)
            self.log(f"Started New Worker (PID: {new_worker.pid})")
            await asyncio.sleep(5)
            
            # Send more messages
            await self.send_batch(MESSAGES_BATCH_2, "Batch2")
            
            # Verify total
            total_expected = MESSAGES_BATCH_1 + MESSAGES_BATCH_2
            success = await self.wait_for_processing(total_expected)
            
            if success:
                self.log("✅ New worker joined and helped process messages.")

        except Exception as e:
            self.log(f"ERROR: Test failed with exception: {e}")
        finally:
            await self.cleanup()
            self.generate_report()

    async def cleanup(self):
        self.add_section("Cleanup")
        for p in self.workers:
            if p.poll() is None:
                p.terminate()
                self.log(f"Terminated Worker (PID: {p.pid})")
        
        if self.client:
            await self.client.aclose()
        db_client.close()

    def generate_report(self):
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(f"# Relatório de Teste de Tolerância a Falhas\n")
            f.write(f"**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("\n".join(self.report_lines))
        print(f"\nReport generated at: {os.path.abspath(REPORT_FILE)}")

if __name__ == "__main__":
    tester = FaultToleranceTester()
    try:
        asyncio.run(tester.run())
    except KeyboardInterrupt:
        pass
