import asyncio
import os
import json
import sqlite3
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

# Parse DATABASE_URL for sqlite path (assuming postgresql+asyncpg://user:pass@host/dbname or similar)
# But earlier log said "Started server process... Database tables initialized". And user has `backend/.env`.
# I'll just try to read the token using a simple SQL query if I can connect.
# If it's Postgres, I need psycopg2. 
# `uv pip install psycopg2-binary` might be needed if not present.
# But `asyncpg` is present.
# trying to avoid dependency hell. I'll just use the token search output I saw earlier if I can.
# Or I'll use `debug_mcp_clean.py` again but cleaner.

# Let's write a script that imports 'mcp' and uses the hardcoded token if I can find it.
# I'll run `debug_mcp_clean.py` one more time and look at the output very carefully.
# Wait, I can just use `app.database.database` if I fix the path?
# I already fixed the import in `probe_auth.py` but then it failed on `app.models`.

# Okay, let's try `test_mcp_conn.py` using `probe_auth.py`'s fixed import logic, 
# BUT removing `McpServerSetting` import and using raw SQL on `AsyncSessionLocal`.

import sys
sys.path.append(os.getcwd())
from app.database.database import AsyncSessionLocal
from sqlalchemy import text

async def get_token():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT credentials FROM mcp_server_settings WHERE server_name LIKE '%GitHub%'"))
        row = result.first()
        if row and row[0]:
            return json.loads(row[0]).get("access_token")
    return None

async def test_conn():
    token = await get_token()
    if not token:
        print("No token found")
        return

    url = "https://api.githubcopilot.com/mcp/"
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Testing SSE to {url}...")
    try:
        async with sse_client(url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("SSE Initialize Success")
                tools = await session.list_tools()
                print(f"SSE Tools: {len(tools.tools)}")
    except Exception as e:
        print(f"SSE Failed: {e}")

    print("\nTesting Streamable HTTP...")
    try:
        async with streamablehttp_client(url, headers=headers) as (read, write, transport):
             async with ClientSession(read, write) as session:
                await session.initialize()
                print("Streamable Initialize Success")
                tools = await session.list_tools()
                print(f"Streamable Tools: {len(tools.tools)}")
                
                # Try run_tool if listing works
                # Assuming 'github_myself' tool exists or similar? 
                # Check tools list first.
                first_tool = tools.tools[0].name if tools.tools else None
                if first_tool:
                     print(f"Running tool {first_tool}...")
                     # Just dry run or minimal?
    except Exception as e:
        print(f"Streamable Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
