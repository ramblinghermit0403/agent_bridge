
import logging
from typing import Dict, Any

from langchain.agents import create_tool_calling_agent


# Import from new modules
from .patches import apply_gemini_patch
from .prompts import build_agent_prompt, build_langgraph_prompt
from .llm_factory import get_llm
from .tools import build_tools_from_servers
from .memory import get_session_memory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply patches on module load to ensure 'finish_reason' fix is active
apply_gemini_patch()

__all__ = ["create_final_agent_pipeline", "get_session_memory", "get_llm"]

async def create_final_agent_pipeline(
    user_mcp_servers: Dict[str, Any], 
    user_id: str = None,
    model_provider: str = "gemini",
    model_name: str = "gemini-2.5-flash"
) -> Any:
    """
    Creates a user-specific AgentExecutor pipeline on-demand.
    Refactored to use modular components:
    - llm_factory: handles provider abstraction
    - tools: handles MCP connection and dynamic creation
    - prompts: handles prompt templates
    """
    
    # 1. Get LLM (Cached via Factory)
    llm = get_llm(model_provider, model_name)
    
    # 2. Build Tools (User Specific)
    # Pass blocking=False because the Graph handles permissions via 'human_review' node/interrupts
    all_tools = await build_tools_from_servers(user_mcp_servers, user_id=user_id, blocking=False)
    

    logger.info(f"Agent created with {len(all_tools)} tools: {[t.name for t in all_tools]}")

    # 3. Initialize Tool Registry & Search Tool
    from .tool_registry import ToolRegistry
    from .tools import create_tool_search_tool
    
    tool_registry = ToolRegistry()
    tool_registry.register_tools(all_tools)
    
    search_tool = create_tool_search_tool(tool_registry, user_id)
    
    # Add search tool to the list of tools available to the agent
    all_tools.append(search_tool)

    # 4. Create LangGraph Agent
    from .agent_orchestrator import create_graph_agent, GraphAgentExecutor
    from langgraph.checkpoint.memory import MemorySaver
    
    # In-memory checkpointer for now (equivalent to previous RAM state but interruptible)
    # For true production persistence across restarts, use Postgres/Redis checkpointer here.
    checkpointer = MemorySaver()
    
    # Use LangGraph specific prompt
    langgraph_prompt = build_langgraph_prompt()
    
    # Pass model_provider to enable conditional tool nodes
    graph = create_graph_agent(llm, all_tools, langgraph_prompt, model_provider=model_provider)
    
    # Compile with checkpointer to enable interrupts
    app = graph.compile(checkpointer=checkpointer, interrupt_before=["human_review"])
    
    # Wrap in compatibility layer
    agent_executor = GraphAgentExecutor(app, checkpointer=checkpointer, tool_registry=tool_registry)
    logger.info("Successfully created LangGraph agent.")
    
    return agent_executor