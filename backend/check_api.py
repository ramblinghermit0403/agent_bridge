import asyncio
import httpx
import json

async def check_api_endpoints():
    base_url = "http://localhost:8001"
    
    # We need a valid token. Since I can't easily login, 
    # I will try to call the preapproved-servers endpoint (which might be protected)
    # Actually, let's checking the open endpoints first.
    
    print("Checking Preapproved Servers (if public)...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{base_url}/api/mcp/preapproved-servers")
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"Data: {json.dumps(resp.json(), indent=2)}")
            else:
                print(f"Error: {resp.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_api_endpoints())
