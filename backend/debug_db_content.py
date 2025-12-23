import asyncio
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def check_connections():
    async with AsyncSessionLocal() as session:
        # Check McpServerSetting
        print("Checking McpServerSetting table...")
        result = await session.execute(text("SELECT id, user_id, server_name, server_url FROM mcp_server_settings"))
        rows = result.fetchall()
        if rows:
            print(f"Found {len(rows)} settings:")
            for row in rows:
                print(f"  ID: {row[0]}, UserID: {row[1]}, Name: {row[2]}, URL: {row[3]}")
        else:
            print("No settings found in mcp_server_settings table.")

        # Check Users to verify IDs
        print("\nChecking Users table...")
        result = await session.execute(text("SELECT id, email FROM \"Users\""))
        rows = result.fetchall()
        for row in rows:
            print(f"  ID: {row[0]}, Email: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check_connections())
