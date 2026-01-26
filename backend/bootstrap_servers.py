import asyncio
import json
import os
import sys

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import database
from app.models.settings import McpServerSetting
from app.models.user import User
from sqlalchemy.future import select

async def bootstrap_servers(email: str):
    """
    Reads servers.json and registers them for the user with the given email.
    """
    config_path = "servers.json"
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return

    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            # Handle both list (legacy) and dict with 'defaults' key
            if isinstance(data, list):
                servers = data
            else:
                servers = data.get("defaults", [])
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in servers.json: {e}")
        return

    async with database.AsyncSessionLocal() as db:
        # 1. Find User
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User not found with email: {email}")
            return
            
        print(f"👤 Found user: {user.email} (ID: {user.id})")

        # 2. Upsert Servers
        for srv in servers:
            name = srv.get("server_name")
            url = srv.get("url")
            desc = srv.get("description", "")
            active = srv.get("is_active", True)
            creds = json.dumps(srv.get("credentials")) if srv.get("credentials") else None
            
            # Check if exists
            stmt = select(McpServerSetting).where(
                McpServerSetting.user_id == user.id,
                McpServerSetting.server_name == name
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"📝 Updating existing server: {name}")
                existing.server_url = url
                existing.description = desc
                existing.is_active = active
                if creds:
                    existing.credentials = creds
            else:
                print(f"➕ Creating new server: {name}")
                new_setting = McpServerSetting(
                    user_id=user.id,
                    server_name=name,
                    server_url=url,
                    description=desc,
                    is_active=active,
                    credentials=creds
                )
                db.add(new_setting)
        
        await db.commit()
        print("\n✅ Server bootstrap complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bootstrap_servers.py <user_email>")
    else:
        user_email = sys.argv[1]
        asyncio.run(bootstrap_servers(user_email))
