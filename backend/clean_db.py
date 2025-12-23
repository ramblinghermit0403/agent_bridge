import asyncio
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def clean_mcp_settings():
    async with AsyncSessionLocal() as session:
        print("Cleaning mcp_server_settings table...")
        await session.execute(text("DELETE FROM mcp_server_settings"))
        await session.commit()
        print("✅ Table cleared. All previous connections removed.")

if __name__ == "__main__":
    asyncio.run(clean_mcp_settings())
