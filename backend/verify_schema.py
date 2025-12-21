import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def verify_columns():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("Checking columns in 'Users' table...")
        # Inspect columns using information_schema
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'Users';"))
        rows = result.fetchall()
        print("Found columns:")
        for row in rows:
            print(f"- {row[0]} ({row[1]})")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_columns())
