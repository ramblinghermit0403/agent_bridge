import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check_approvals():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT tool_name, approval_type FROM tool_approvals WHERE user_id = :user_id"),
            {"user_id": "0aa9b3ed-c25a-4f9c-8a3a-70e02e5954c1"}
        )
        approvals = result.fetchall()
        
        if approvals:
            print("Tool Approvals:")
            for row in approvals:
                print(f"  {row.tool_name}: {row.approval_type}")
        else:
            print("No tool approvals found - all tools will require per-use approval by default")

asyncio.run(check_approvals())
