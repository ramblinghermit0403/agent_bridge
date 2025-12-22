import asyncio
import httpx
import json

async def register_client():
    """Register a client with Notion MCP using Dynamic Client Registration (RFC 7591)"""
    
    registration_endpoint = "https://mcp.notion.com/register"
    
    # Client metadata for registration
    client_metadata = {
        "client_name": "Agent Bridge",
        "redirect_uris": ["http://localhost:8001/api/mcp/oauth/callback"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_basic",  # or "none" for PKCE-only
        "scope": ""
    }
    
    print(f"Registering client with Notion MCP...")
    print(f"Registration endpoint: {registration_endpoint}")
    print(f"Client metadata: {json.dumps(client_metadata, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                registration_endpoint,
                json=client_metadata,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\nStatus: {resp.status_code}")
            print(f"Response: {json.dumps(resp.json(), indent=2)}")
            
            if resp.status_code in [200, 201]:
                data = resp.json()
                print(f"\n✅ Client registered successfully!")
                print(f"\nClient ID: {data.get('client_id')}")
                print(f"Client Secret: {data.get('client_secret')}")
                print(f"\n⚠️  IMPORTANT: Add these to your .env file:")
                print(f"NOTION_CLIENT_ID={data.get('client_id')}")
                print(f"NOTION_CLIENT_SECRET={data.get('client_secret')}")
                
                # Save to file
                with open("notion_client_credentials.json", "w") as f:
                    json.dump(data, f, indent=2)
                print(f"\nCredentials saved to: notion_client_credentials.json")
            else:
                print(f"\n❌ Registration failed: {resp.text}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(register_client())
