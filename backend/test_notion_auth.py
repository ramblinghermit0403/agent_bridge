import asyncio
import httpx
import json
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def test_notion_auth():
    # Get token from DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT credentials FROM mcp_server_settings WHERE id = 13")
        )
        row = result.first()
        if not row or not row[0]:
            print("No credentials found")
            return
        
        creds = json.loads(row[0])
        token = creds.get('access_token')
        
        if not token:
            print("No access_token in credentials")
            return
        
        print(f"Token (first 20 chars): {token[:20]}...")
    
    # Test 1: Notion REST API (should work)
    print("\n=== Test 1: Notion REST API ===")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://api.notion.com/v1/users/me",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28"
                }
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 2: Notion MCP (currently failing)
    print("\n=== Test 2: Notion MCP Server ===")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://mcp.notion.com/mcp",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
            )
            print(f"Status: {resp.status_code}")
            print(f"Headers: {dict(resp.headers)}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_notion_auth())
