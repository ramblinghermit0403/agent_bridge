import asyncio
import httpx
import json

async def check_figma_oauth_metadata():
    """Check if Figma MCP exposes OAuth 2.1 metadata (RFC 8414)"""
    
    # Standard OAuth metadata endpoints and potential Figma specifics
    metadata_urls = [
        "https://mcp.figma.com/.well-known/oauth-authorization-server",
        "https://api.figma.com/.well-known/oauth-authorization-server",
        "https://www.figma.com/.well-known/oauth-authorization-server",
        "https://mcp.figma.com/mcp/.well-known/oauth-authorization-server",
        # Sometimes it's at the root of the issuer
        "https://figma.com/.well-known/oauth-authorization-server"
    ]
    
    results = []
    async with httpx.AsyncClient() as client:
        for url in metadata_urls:
            print(f"Testing: {url}...")
            result = {"url": url}
            try:
                # Follow redirects might be needed
                resp = await client.get(url, timeout=5.0, follow_redirects=True)
                result["status"] = resp.status_code
                if resp.status_code == 200:
                    try:
                        result["metadata"] = resp.json()
                        print(f"✅ Found metadata at {url}!")
                    except json.JSONDecodeError:
                        result["error"] = "Response was not JSON"
                else:
                    result["error"] = f"Status {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                result["error"] = str(e)
            results.append(result)
    
    # Write to file
    with open("figma_metadata_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults written to figma_metadata_results.json")
    
    # Print summary
    found = False
    for r in results:
        if r.get("status") == 200 and "metadata" in r:
            found = True
            print(f"\n✅ Found at: {r['url']}")
            m = r['metadata']
            print(f"  Issuer: {m.get('issuer')}")
            print(f"  Authorization: {m.get('authorization_endpoint')}")
            print(f"  Token: {m.get('token_endpoint')}")
    
    if not found:
        print("\n❌ No OAuth metadata found at standard endpoints for Figma.")

if __name__ == "__main__":
    asyncio.run(check_figma_oauth_metadata())
