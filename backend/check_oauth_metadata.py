import asyncio
import httpx
import json

async def check_notion_oauth_metadata():
    """Check if Notion MCP exposes OAuth 2.1 metadata (RFC 8414)"""
    
    # Standard OAuth metadata endpoints
    metadata_urls = [
        "https://mcp.notion.com/.well-known/oauth-authorization-server",
        "https://api.notion.com/.well-known/oauth-authorization-server",
        "https://mcp.notion.com/mcp/.well-known/oauth-authorization-server"
    ]
    
    results = []
    async with httpx.AsyncClient() as client:
        for url in metadata_urls:
            result = {"url": url}
            try:
                resp = await client.get(url, timeout=5.0)
                result["status"] = resp.status_code
                if resp.status_code == 200:
                    result["metadata"] = resp.json()
                else:
                    result["error"] = resp.text[:200]
            except Exception as e:
                result["error"] = str(e)
            results.append(result)
    
    # Write to file
    with open("oauth_metadata_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Results written to oauth_metadata_results.json")
    
    # Print summary
    for r in results:
        if r.get("status") == 200:
            print(f"\n✅ Found at: {r['url']}")
            m = r['metadata']
            print(f"  Authorization: {m.get('authorization_endpoint')}")
            print(f"  Token: {m.get('token_endpoint')}")

if __name__ == "__main__":
    asyncio.run(check_notion_oauth_metadata())
