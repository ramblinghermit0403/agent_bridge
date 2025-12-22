import asyncio
import httpx
import json
from sqlalchemy import select
from app.database.database import AsyncSessionLocal
from app.models.settings import McpServerSetting

async def verify_token():
    async with AsyncSessionLocal() as session:
        # Fetch the Figma setting (assuming it is the one we are working on)
        result = await session.execute(select(McpServerSetting).where(McpServerSetting.server_name == 'Figma'))
        setting = result.scalars().first()
        
        if not setting or not setting.credentials:
            print("No Figma settings or credentials found.")
            return

        creds = json.loads(setting.credentials)
        token = creds.get('access_token')
        
        print(f"Checking token: {token[:10]}...")
        
        # Test against Figma API
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.figma.com/v1/me", 
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Figma API /me status: {resp.status_code}")
            print(f"Response: {resp.text}")
        token = creds.get('access_token')
        
        print(f"Checking token: {token[:10]}...")
        
        # Test against Figma API
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.figma.com/v1/me", 
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Figma API /me status: {resp.status_code}")
            print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(verify_token())
