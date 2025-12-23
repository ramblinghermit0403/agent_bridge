import asyncio
import httpx
import json

async def register_figma_client():
    """Register a client with Figma MCP using Dynamic Client Registration"""
    
    registration_endpoint = "https://api.figma.com/v1/oauth/mcp/register"
    
    # Client metadata for registration
    client_metadata = {
        "client_name": "Agent Bridge",
        "redirect_uris": ["http://localhost:8001/api/mcp/oauth/callback"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_basic",
        "scope": "mcp:connect"
    }
    
    print(f"Registering client with Figma MCP...")
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
            try:
                print(f"Response: {json.dumps(resp.json(), indent=2)}")
            except:
                print(f"Response Text: {resp.text}")
            
            if resp.status_code in [200, 201]:
                data = resp.json()
                print(f"\n✅ Client registered successfully!")
                print(f"\nClient ID: {data.get('client_id')}")
                print(f"Client Secret: {data.get('client_secret')}")
                print(f"\n⚠️  IMPORTANT: Add these to your .env file:")
                print(f"FIGMA_CLIENT_ID={data.get('client_id')}")
                print(f"FIGMA_CLIENT_SECRET={data.get('client_secret')}")
                
                # Save to file
                with open("figma_client_credentials.json", "w") as f:
                    json.dump(data, f, indent=2)
                print(f"\nCredentials saved to: figma_client_credentials.json")
            else:
                print(f"\n❌ Registration failed.")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(register_figma_client())
