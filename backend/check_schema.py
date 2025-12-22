import asyncio
from sqlalchemy import text
from app.database import database

async def check_schema():
    async with database.engine.connect() as conn:
        result = await conn.execute(text("PRAGMA table_info(mcp_server_settings)"))
        columns = result.fetchall()
        print("Columns in mcp_server_settings:")
        for col in columns:
            print(col)

if __name__ == "__main__":
    asyncio.run(check_schema())
