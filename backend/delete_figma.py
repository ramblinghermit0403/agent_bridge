import asyncio
from sqlalchemy import text
from app.database.database import AsyncSessionLocal

async def delete_figma_connection():
    """Delete the old Figma connection so user can reconnect with correct OAuth endpoints"""
    async with AsyncSessionLocal() as session:
        # Find Figma connection
        result = await session.execute(
            text("SELECT id, server_name FROM mcp_server_settings WHERE server_name = 'Figma'")
        )
        rows = result.fetchall()
        
        if not rows:
            print("No Figma connections found.")
            return
        
        print(f"Found {len(rows)} Figma connection(s):")
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
        print("\n✅ All Figma connections deleted. Please reconnect in the UI.")

if __name__ == "__main__":
    asyncio.run(delete_figma_connection())
