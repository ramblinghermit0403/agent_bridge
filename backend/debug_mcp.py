import asyncio
import httpx
import logging

# Hardcoded token from recent successful DB read (or I'll fetch it again cleanly if I can't find it)
# Wait, I don't have the token string. I must fetch it.
# I will use a minimal sqlite script.

import sqlite3
import json

async def debug_mcp():
    # 1. Get Token via raw sqlite to avoid SA logging issues
    # Find the db file? DATABASE_URL is in .env. 
    # Usually 'sqlite:///./sql_app.db' or similar.
    # But wait, looking at logs, it's Postgres? 
    # "SELECT ... FROM "Users" ..."
    # "sqlalchemy.engine.Engine select pg_catalog.version()"
    # It IS Postgres. I can't use sqlite3.
    
    # Okay, I will use asyncpg directly? No, I don't know if it's installed.
    # I will stick to SA but configure it carefully.
    
    # Or I can just trust the logging config this time.
    pass

import sys

# Configure logging to console, only ERROR level for root
logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

from app.database.database import AsyncSessionLocal
from app.models.settings import McpServerSetting
from sqlalchemy import select, desc

async def run():
    print("--- STARTING DEBUG ---", flush=True)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(McpServerSetting)
            .where(McpServerSetting.server_name == 'Figma')
            .order_by(desc(McpServerSetting.id))
        )
        setting = result.scalars().first()
        if not setting: 
            print("No setting found", flush=True)
            return
        
        creds = json.loads(setting.credentials)
        token = creds.get('access_token')
        print(f"Token: {token[:10]}...", flush=True)
        url = setting.server_url
        print(f"URL: {url}", flush=True)
        
        async with httpx.AsyncClient() as client:
            print(f"Testing POST {url}", flush=True)
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}
            )
            print(f"Status: {resp.status_code}", flush=True)
            print(f"Body: {resp.text}", flush=True)
            print(f"Headers: {resp.headers}", flush=True)

if __name__ == "__main__":
    asyncio.run(run())
