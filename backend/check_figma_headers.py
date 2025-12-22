import httpx
import asyncio

async def check_auth_header():
    url = "https://mcp.figma.com/mcp"
    print(f"Connecting to {url}...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            print(f"Status Code: {resp.status_code}")
            print(f"Headers: {resp.headers}")
            if "www-authenticate" in resp.headers:
                print(f"WWW-Authenticate: {resp.headers['www-authenticate']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_auth_header())
