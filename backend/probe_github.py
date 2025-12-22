import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = "https://api.githubcopilot.com/mcp/"
TOKEN_URL = "https://github.com/login/oauth/access_token"
# We need a token. I'll assume we can't easily get a fresh one here without flow, 
# but I can try probing without token or use the one from DB if I could.
# checking methods usually doesn't need auth for 405 vs 401/403 check.

async def probe():
    async with httpx.AsyncClient() as client:
        print(f"--- Probing {SERVER_URL} ---")
        
        # 1. OPTIONS
        try:
            resp = await client.options(SERVER_URL)
            print(f"OPTIONS: {resp.status_code}")
            print(f"Allow header: {resp.headers.get('allow')}")
        except Exception as e:
            print(f"OPTIONS failed: {e}")

        # 2. GET (SSE probe)
        try:
            headers = {"Accept": "text/event-stream"}
            resp = await client.get(SERVER_URL, headers=headers)
            print(f"GET (SSE): {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type')}")
        except Exception as e:
            print(f"GET failed: {e}")

        # 3. POST (RPC probe - empty)
        try:
            resp = await client.post(SERVER_URL, json={}, headers={"Content-Type": "application/json"})
            print(f"POST (Empty): {resp.status_code}")
        except Exception as e:
            print(f"POST failed: {e}")

        # 4. GET /sse subpath
        try:
            url_sse = SERVER_URL.rstrip('/') + "/sse"
            resp = await client.get(url_sse, headers={"Accept": "text/event-stream"})
            print(f"GET /sse: {resp.status_code}")
        except Exception as e:
             print(f"GET /sse failed: {e}")

if __name__ == "__main__":
    asyncio.run(probe())
