import httpx
import asyncio

async def fetch_metadata():
    url = "https://mcp.figma.com/.well-known/oauth-authorization-server"
    print(f"Fetching metadata from {url}...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_metadata())
