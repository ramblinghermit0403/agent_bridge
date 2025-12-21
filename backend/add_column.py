import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def add_column():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        try:
            print("Attempting to add 'is_guest' column...")
            await conn.execute(text('ALTER TABLE "Users" ADD COLUMN is_guest BOOLEAN DEFAULT FALSE;'))
            print("Successfully added 'is_guest' column.")
        except Exception as e:
            print(f"Error adding column (maybe it exists?): {e}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_column())
