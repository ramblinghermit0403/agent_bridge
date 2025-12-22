import httpx
import asyncio
import os
import json
import sqlite3
# Manually reading sqlite db to avoid async issues with sqlalchemy in simple script
# The db is at ./brain_vault.db (or check env)
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DATABASE_URL")
# DB_URL is usually postgresql+asyncpg://... but user might be local sqlite?
# Actually user info says "The user's OS version is windows. c:\Users\himan\OneDrive\Documents\ai agent mcp"
# But database.py uses DATABASE_URL.
# If it's postgres, I need asyncpg or psycopg2.
# "Migrating the relational database: Switching from SQLite to PostgreSQL, which has been successfully completed"
# So it is Postgres.

# I'll use raw string manipulation to get connection params or just use my existing backend code to fetch it?
# Using existing backend code is cleaner but requires async setup.
# I'll modify `debug_mcp_clean.py` logic to fetch token.

import sys
from app.database.database import AsyncSessionLocal
from app.models.mcp_server_setting import McpServerSetting
from sqlalchemy import select

async def get_github_token():
    async with AsyncSessionLocal() as db:
        stmt = select(McpServerSetting).where(McpServerSetting.server_name.ilike("%GitHub%"))
        result = await db.execute(stmt)
        setting = result.scalars().first()
        if setting and setting.credentials:
             creds = json.loads(setting.credentials)
             return creds.get("access_token")
    return None

SERVER_URL = "https://api.githubcopilot.com/mcp/"

async def probe():
    token = await get_github_token()
    if not token:
        print("No GitHub token found in DB.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream"
    }

    async with httpx.AsyncClient() as client:
        print(f"--- Probing {SERVER_URL} with Token ---")
        
        # 1. GET (SSE)
        try:
            print("Sending GET...")
            resp = await client.get(SERVER_URL, headers=headers)
            print(f"GET (SSE): {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type')}")
            print(f"Body snippet: {resp.text[:100]}")
        except Exception as e:
            print(f"GET failed: {e}")

        # 2. POST
        try:
            print("Sending POST...")
            # Headers for POST
            p_headers = headers.copy()
            p_headers["Content-Type"] = "application/json"
            # Minimal Initialize? Or just empty? 
            # Empty POST might error 400, but we check for 405.
            resp = await client.post(SERVER_URL, json={"jsonrpc":"2.0","method":"ping","id":1}, headers=p_headers)
            print(f"POST(Ping): {resp.status_code}")
            print(f"Body: {resp.text[:100]}")
        except Exception as e:
             print(f"POST failed: {e}")

if __name__ == "__main__":
    # Add path to sys to find app
    sys.path.append(os.getcwd())
    asyncio.run(probe())
