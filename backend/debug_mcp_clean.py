import asyncio
import httpx
import json
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load env manually
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def run():
    print("--- STARTING CLEAN DEBUG ---", flush=True)
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    token = None
    url = None

    async with async_session() as session:
        # Raw SQL to avoid model imports and logging noise
        result = await session.execute(text("SELECT credentials, server_url FROM mcp_server_settings WHERE server_name LIKE '%GitHub%' ORDER BY id DESC LIMIT 1"))
        row = result.first()
        if not row:
            print("No setting found", flush=True)
            return
        
        creds_json = row[0]
        url = row[1]
        try:
            creds = json.loads(creds_json)
            token = creds.get('access_token')
        except:
            pass

    if not token:
        print("No token found", flush=True)
        return

    print(f"Target URL: {url}", flush=True)
    print(f"Token: {token[:10]}...", flush=True)

    async with httpx.AsyncClient() as client:
        # 1. Verify Token against /me
        print("\n[1] Checking /v1/me...", flush=True)
        r1 = await client.get("https://api.figma.com/v1/me", headers={"Authorization": f"Bearer {token}"})
        print(f"Status: {r1.status_code}", flush=True)
        print(f"Body: {r1.text[:200]}", flush=True) # Truncate for sanity

        # 2. Check MCP Endpoint with Bearer
        print(f"\n[2] Checking MCP {url} (Bearer)...", flush=True)
        try:
            r2 = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
            )
            print(f"Status: {r2.status_code}", flush=True)
            print(f"Headers: {r2.headers}", flush=True)
            print(f"Body: {r2.text}", flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)

        # 3. Check MCP Endpoint with X-Figma-Token
        print(f"\n[3] Checking MCP {url} (X-Figma-Token)...", flush=True)
        try:
            r3 = await client.post(
                url,
                headers={"X-Figma-Token": token, "Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
            )
            print(f"Status: {r3.status_code}", flush=True)
            print(f"WWW-Authenticate: {r3.headers.get('www-authenticate')}", flush=True)
            print(f"Body: {r3.text}", flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)

        # 4. Check MCP Endpoint with Figma-Token
        print(f"\n[4] Checking MCP {url} (Figma-Token)...", flush=True)
        try:
            r4 = await client.post(
                url,
                headers={"Figma-Token": token, "Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
            )
            print(f"Status: {r4.status_code}", flush=True)
            print(f"Body: {r4.text}", flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)
            
        # 5. Check OPTIONS (CORS?)
        print(f"\n[5] Checking OPTIONS {url}...", flush=True)
        try:
            r5 = await client.options(url)
            print(f"Status: {r5.status_code}", flush=True)
            print(f"Allow: {r5.headers.get('allow')}", flush=True)
        except Exception as e:
             print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(run())
