import asyncio
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def check_notion():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT id, server_name, server_url, is_active FROM mcp_server_settings WHERE server_name LIKE '%Notion%'")
        )
        rows = result.fetchall()
        if rows:
            print("Found Notion connections:")
            for row in rows:
                print(f"  ID: {row[0]}, Name: {row[1]}, URL: {row[2]}, Active: {row[3]}")
        else:
            print("No Notion connections found in database")

if __name__ == "__main__":
    asyncio.run(check_notion())
