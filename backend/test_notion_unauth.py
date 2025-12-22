import asyncio
import httpx

async def test_notion_mcp_unauthenticated():
    """Test if Notion MCP works without any auth headers"""
    
    print("=== Test 1: Notion MCP without auth ===")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://mcp.notion.com/mcp",
                headers={"Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n=== Test 2: Notion MCP with only Content-Type ===")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://mcp.notion.com/mcp",
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}}
            )
            print(f"Status: {resp.status_code}")
            print(f"Headers: {dict(resp.headers)}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_notion_mcp_unauthenticated())
