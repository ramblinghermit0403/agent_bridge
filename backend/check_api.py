import httpx
import asyncio
import sys

async def check():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("http://localhost:8001/api/mcp/preapproved-servers")
            data = resp.json()
            
            gh = next((s for s in data if s["server_name"] == "GitHub"), None)
            if gh:
                conf = gh.get("oauth_config", {})
                cid = conf.get("client_id")
                print(f"Server Name: {gh['server_name']}")
                print(f"Client ID in response: {cid}")
                print(f"Is Client ID None? {cid is None}")
            else:
                print("GitHub not found")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
