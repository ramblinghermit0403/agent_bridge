import httpx
import asyncio

async def check_auth_header_post():
    url = "https://mcp.figma.com/mcp"
    print(f"Connecting to {url} with POST...")
    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05", # Dummy version
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        },
        "id": 1
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload)
            print(f"Status Code: {resp.status_code}")
            print(f"Headers: {resp.headers}")
            if "www-authenticate" in resp.headers:
                print(f"WWW-Authenticate: {resp.headers['www-authenticate']}")
            else:
                print("No WWW-Authenticate header found.")
                print(f"Body: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_auth_header_post())
