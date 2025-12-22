
import asyncio
from sqlalchemy import text
from app.database import database

async def add_column():
    print("Connecting to database...")
    async with database.engine.begin() as conn:
        try:
            # Check if column exists (Postgres specific check, but works for SQLite too with simple ALTER)
            # Simpler: Try to add it, if it fails, assuming it exists.
            print("Attempting to add 'credentials' column to mcp_server_settings...")
            await conn.execute(text("ALTER TABLE mcp_server_settings ADD COLUMN credentials TEXT"))
            print("Column 'credentials' added successfully.")
        except Exception as e:
            print(f"Migration result (probably already exists): {e}")

if __name__ == "__main__":
    asyncio.run(add_column())
