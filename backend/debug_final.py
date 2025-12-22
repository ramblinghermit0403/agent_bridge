import asyncio
import httpx
import json
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
import sys

# Load env manually
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def run():
    print("--- DEBUG FINAL START ---", flush=True)
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    token = None
    url = None

    async with async_session() as session:
        result = await session.execute(text("SELECT credentials, server_url FROM mcp_server_settings WHERE server_name = 'Figma' ORDER BY id DESC LIMIT 1"))
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

    print(f"URL: {url}", flush=True)
    
    # Payload for JSON-RPC verify
    payload = {
        "jsonrpc": "2.0", 
        "method": "initialize", 
        "params": {
            "protocolVersion": "2024-11-05", 
            "capabilities": {}, 
            "clientInfo": {"name": "test", "version": "1.0"}
        }, 
        "id": 1
    }

    async with httpx.AsyncClient() as client:
        # 1. Bearer
        # print("\n[1] TEST: Authorization: Bearer <token>", flush=True)
        # try:
        #     r = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        #     print(f"Status: {r.status_code}", flush=True)
        #     print(f"Headers: {r.headers}", flush=True)
        #     print(f"Body: {r.text}", flush=True)
        # except Exception as e:
        #     print(f"Ex: {e}", flush=True)

        # 2. X-Figma-Token
        print("\n[2] TEST: X-Figma-Token: <token>", flush=True)
        try:
            r = await client.post(url, json=payload, headers={"X-Figma-Token": token})
            print(f"Status: {r.status_code}", flush=True)
            print(f"Headers: {r.headers}", flush=True)
            print(f"Body: {r.text}", flush=True)
        except Exception as e:
            print(f"Ex: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(run())
