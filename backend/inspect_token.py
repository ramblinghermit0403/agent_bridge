import asyncio
import json
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def inspect_token():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT credentials FROM mcp_server_settings WHERE id = 13")
        )
        row = result.first()
        if row and row[0]:
            creds = json.loads(row[0])
            print("Full credentials structure:")
            print(json.dumps(creds, indent=2))
            
            if 'access_token' in creds:
                token = creds['access_token']
                print(f"\nAccess token length: {len(token)}")
                print(f"Access token preview: {token[:50]}...")
                print(f"Token type: {type(token)}")
                
                # Check if it looks like a JWT or other format
                if token.count('.') == 2:
                    print("Format: Looks like a JWT (3 parts separated by dots)")
                elif token.startswith('secret_'):
                    print("Format: Looks like a Notion internal integration token")
                else:
                    print(f"Format: Unknown (starts with: {token[:20]})")

if __name__ == "__main__":
    asyncio.run(inspect_token())
