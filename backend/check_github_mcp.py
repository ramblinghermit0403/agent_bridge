import httpx
import asyncio

async def check():
    url = "https://api.githubcopilot.com/mcp/"
    print(f"Connecting to {url}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            print(f"Status: {resp.status_code}")
            print(f"Headers: {resp.headers}")
            print(f"Body: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
