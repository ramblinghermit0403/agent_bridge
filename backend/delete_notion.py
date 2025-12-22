import asyncio
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def delete_notion_connection():
    """Delete the old Notion connection so user can reconnect with PKCE"""
    async with AsyncSessionLocal() as session:
        # Find Notion connection
        result = await session.execute(
            text("SELECT id, server_name FROM mcp_server_settings WHERE server_name LIKE '%Notion%'")
        )
        rows = result.fetchall()
        
        if not rows:
            print("No Notion connections found.")
            return
        
        print(f"Found {len(rows)} Notion connection(s):")
        for row in rows:
            print(f"  ID: {row[0]}, Name: {row[1]}")
        
        # Delete them
        for row in rows:
            await session.execute(
                text("DELETE FROM mcp_server_settings WHERE id = :id"),
                {"id": row[0]}
            )
            print(f"✅ Deleted connection ID {row[0]}")
        
        await session.commit()
        print("\n✅ All Notion connections deleted. Please reconnect in the UI.")

if __name__ == "__main__":
    asyncio.run(delete_notion_connection())
