import httpx
import asyncio

async def test_oauth_init():
    url = "http://localhost:8001/api/mcp/oauth/init"
    payload = {
        "server_name": "Figma",
        "client_id": "gjzhf9kPyHZpb6DMjZ8r5b",
        "client_secret": "",
        "redirect_uri": "http://localhost:8001/api/mcp/oauth/callback"
    }
    
    print(f"Sending payload: {payload}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_oauth_init())
