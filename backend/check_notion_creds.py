import asyncio
import json
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def check_notion_creds():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT id, server_name, credentials FROM mcp_server_settings WHERE id = 12")
        )
        row = result.first()
        if row:
            print(f"ID: {row[0]}")
            print(f"Server: {row[1]}")
            if row[2]:
                creds = json.loads(row[2])
                print(f"Credentials keys: {list(creds.keys())}")
                # Print first few chars of token
                if 'access_token' in creds:
                    token = creds['access_token']
                    print(f"Access token (first 20 chars): {token[:20]}...")
                    print(f"Access token length: {len(token)}")
                print(f"Full credentials structure: {json.dumps(creds, indent=2)}")
            else:
                print("No credentials found")
        else:
            print("Setting ID 12 not found")

if __name__ == "__main__":
    asyncio.run(check_notion_creds())
