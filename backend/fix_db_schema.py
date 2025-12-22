import asyncio
from sqlalchemy import text
from app.database import database

async def fix_schema():
    print("Checking database schema...")
    async with database.engine.begin() as conn:
        # Check if credentials column exists
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='mcp_server_settings' AND column_name='credentials'"
        ))
        row = result.fetchone()
        
        if row:
            print("✅ 'credentials' column already exists.")
        else:
            print("⚠️ 'credentials' column missing. Adding it now...")
            try:
                await conn.execute(text("ALTER TABLE mcp_server_settings ADD COLUMN credentials TEXT"))
                print("✅ 'credentials' column added successfully.")
            except Exception as e:
                print(f"❌ Failed to add column: {e}")

if __name__ == "__main__":
    asyncio.run(fix_schema())
