import asyncio
import json
import base64
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def decode_token():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT credentials FROM mcp_server_settings WHERE id = 13")
        )
        row = result.first()
        if row and row[0]:
            creds = json.loads(row[0])
            token = creds.get('access_token', '')
            
            print(f"Original token (first 50 chars): {token[:50]}...")
            print(f"Token length: {len(token)}")
            
            # Try to decode as base64
            try:
                decoded = base64.b64decode(token).decode('utf-8')
                print(f"\nBase64 decoded: {decoded[:100]}...")
            except Exception as e:
                print(f"\nNot base64 encoded (or decode failed): {e}")
            
            # Check if it's a proper Notion token format
            if token.startswith('secret_'):
                print("\nFormat: Notion internal integration token")
            elif token.startswith('ntn_'):
                print("\nFormat: Notion OAuth token")  
            else:
                print(f"\nFormat: Unknown (starts with '{token[:10]}')")

if __name__ == "__main__":
    asyncio.run(decode_token())
