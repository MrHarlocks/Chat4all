import httpx
import asyncio

async def check_health():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            print("Checking health...")
            resp = await client.get("/health")
            print(f"Health Status: {resp.status_code}")
            print(resp.json())
        except Exception as e:
            print(f"Health Check Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_health())
