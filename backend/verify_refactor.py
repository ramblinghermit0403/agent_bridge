import sys
import os
import asyncio
import logging

# Add backend to path so imports work
sys.path.append(os.getcwd())

# Setup logging
logging.basicConfig(level=logging.INFO)

async def verify():
    print("Attempting to import create_final_agent_pipeline...")
    try:
        from app.services.Agent.langchain_agent import create_final_agent_pipeline, get_session_memory
        print("Import successful (including get_session_memory). Attempting to create agent...")
        
        # Mock data
        user_mcp_servers = {}
        user_id = "test_user"
        
        # This will trigger get_llm, ensure environment is set or handle error
        if not os.environ.get("GOOGLE_API_KEY"):
            print("WARNING: GOOGLE_API_KEY not set, LLM creation might fail or warn.")
        
        agent_executor = await create_final_agent_pipeline(
            user_mcp_servers=user_mcp_servers,
            user_id=user_id,
            model_provider="gemini", 
            model_name="gemini-2.5-flash"
        )
        print("Successfully created agent executor!")
        print(f"Agent tools: {len(agent_executor.tools)}")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(verify())
    if not success:
        sys.exit(1)
