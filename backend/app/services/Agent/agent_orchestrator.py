import logging
import asyncio
import json
from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Union, Optional
from langchain_core.messages import BaseMessage, FunctionMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode

from .tools import build_tools_from_servers
from .llm_factory import get_llm
from .prompts import build_agent_prompt
from app.services.security.permissions import check_tool_approval, PendingApproval
from app.database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # We can add more state here like 'pending_approval' if needed

# --- Node Logic ---

async def sub_agent_node(state: AgentState, llm=None, tools=None, prompt=None, *, config: RunnableConfig = None):
    """
    The main agent node that calls the LLM.
    Dependencies (llm, tools, prompt) are injected via partial binding.
    config is passed by LangGraph as a keyword argument.
    """
    logger.info(f"sub_agent_node: Entering with {len(state['messages'])} messages")
    
    if not llm or not tools or not prompt:
        raise ValueError("Configuration missing LLM, tools, or prompt")

    # Bind tools to LLM
    logger.info(f"sub_agent_node: Binding {len(tools)} tools to LLM: {[t.name for t in tools[:3]]}...")
    llm_with_tools = llm.bind_tools(tools)
    
    # Run chain
    chain = prompt | llm_with_tools
    response = await chain.ainvoke(state)
    
    logger.info(f"sub_agent_node: Got response type={type(response).__name__}, content_length={len(str(response.content)) if hasattr(response, 'content') else 0}, tool_calls={len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0}")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.info(f"sub_agent_node: Tool calls: {[tc['name'] for tc in response.tool_calls]}")
    
    return {"messages": [response]}

async def human_review_node(state: AgentState, config: RunnableConfig):
    """
    Node that handles human review result.
    Checks if the tool was approved or denied, and modifies state accordingly.
    CRITICAL: Defaults to BLOCKING if no explicit approval is found.
    """
    logger.info("--- Human Review Node Reached ---")
    
    # Get user_id from config
    user_id = config.get("configurable", {}).get("user_id")
    
    if not user_id:
        return {}
    
    # Check if there are any denied approvals for this user
    from app.services.security.permissions import PendingApproval
    from langchain_core.messages import ToolMessage
    
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    new_messages = []
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_id = tool_call.get("id", "")
            
            # Find the pending approval for this tool
            found_approval = False
            is_approved = False
            
            for pid, data in list(PendingApproval._pending.items()):
                if data['user_id'] == user_id and data['tool_name'] == tool_name:
                    found_approval = True
                    
                    if data['approved'] is True:
                        is_approved = True
                        logger.info(f"Tool {tool_name} was APPROVED by user")
                        # Don't remove yet, let tool_node clean up after execution
                    elif data['approved'] is False:
                        logger.info(f"Tool {tool_name} was DENIED by user")
                        new_messages.append(
                            ToolMessage(
                                content=f"Error: User explicitly denied execution of tool '{tool_name}'.",
                                tool_call_id=tool_id,
                                name=tool_name
                            )
                        )
                        PendingApproval.remove(pid)
                    else:  # approved is None (still pending, user hasn't acted)
                        logger.warning(f"Tool {tool_name} is still pending approval - blocking execution")
                        new_messages.append(
                            ToolMessage(
                                content=f"Error: Tool '{tool_name}' is awaiting user approval.",
                                tool_call_id=tool_id,
                                name=tool_name
                            )
                        )
                        # Don't remove, keep it pending for resume
                    break
            
            # CRITICAL FIX: If no pending approval found, block by default (fail-safe)
            if not found_approval:
                logger.warning(f"No pending approval found for tool {tool_name} - blocking by default")
                new_messages.append(
                    ToolMessage(
                        content=f"Error: Tool '{tool_name}' requires user approval but no approval record was found.",
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
    
    if new_messages:
        return {"messages": new_messages}
    
    return {}

# --- Conditional Logic ---

async def route_tools(state: AgentState, config: RunnableConfig) -> str:
    """
    Decides whether to go to tools, human_review, or end.
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If no tool calls, end
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return END

    # Check permissions for EACH tool call
    user_id = config.get("configurable", {}).get("user_id")
    tool_calls = last_message.tool_calls
    
    requires_approval = False
    
    # We need to check permissions against DB
    if user_id:
        async with AsyncSessionLocal() as db:
            from app.models import ToolApproval
            from sqlalchemy.future import select
            from datetime import datetime

            # Attempt to strip server prefix if present (format: ServerName_ToolName)
            # This is heuristic but necessary given the deduplication logic.
            from ...services.agent.tools import _deduplicate_tool_names # Just for reference
            
            # Check all tools in one batch query
            actual_tool_calls = [tc for tc in tool_calls if tc["name"] != "search_tools"]
            
            if actual_tool_calls:
                # Sanitize tool names for DB check
                # We assume the user approves the "Raw" tool name or we need to store the unique name.
                # Currently permissions logic seems to use RAW names.
                # We'll try to check BOTH unique name and raw name (by splitting).
                
                names_to_check = []
                for tc in actual_tool_calls:
                    t_name = tc["name"]
                    names_to_check.append(t_name)
                    if "_" in t_name:
                         # Try stripping first part (ServerName_ToolName)
                         parts = t_name.split("_", 1)
                         if len(parts) == 2:
                             names_to_check.append(parts[1])

                try:
                    stmt = select(ToolApproval).where(
                        ToolApproval.user_id == user_id,
                        ToolApproval.tool_name.in_(names_to_check)
                    )
                    result = await db.execute(stmt)
                    # Map both raw and unique names if found
                    approvals = result.scalars().all()
                    approval_map = {}
                    for a in approvals:
                        approval_map[a.tool_name] = a
                        
                except Exception as e:
                     logger.error(f"Error checking tool approvals: {e}")
                     approval_map = {} # Fail allowed (fallback to needs_approval=True)

                for tool_call in actual_tool_calls:
                    tool_name = tool_call["name"]
                    
                    # Whitelist internal tools
                    if tool_name.startswith("_"):
                        continue
                        
                    # Check unique name then raw name
                    approval = approval_map.get(tool_name)
                    if not approval and "_" in tool_name:
                         raw_name = tool_call["name"].split("_", 1)[1]
                         approval = approval_map.get(raw_name)

                    needs_approval = True
                    
                    if approval:
                        # Check expiry
                        is_expired = approval.expires_at and approval.expires_at < datetime.utcnow()
                        if not is_expired and approval.approval_type == 'always':
                            needs_approval = False
                    
                    if needs_approval:
                        requires_approval = True
                        # We must store the EXACT name the agent used, so the UI can match it later
                        approval_id = PendingApproval.create(
                            user_id=user_id,
                            tool_name=tool_name, 
                            server_name="unknown",
                            tool_input=tool_call.get('args', {})
                        )
                        logger.info(f"Blocking tool {tool_name} for approval. Created PendingApproval ID: {approval_id}")
                    
    if requires_approval:
        return "human_review"
    else:
        return "tools"

# --- Graph Construction ---

def create_graph_agent(llm, tools, prompt):
    """
    Builds the compiled StateGraph.
    """
    workflow = StateGraph(AgentState)

from functools import partial

# ...

# --- Graph Construction ---

def create_graph_agent(llm, tools, prompt, model_provider="gemini"):
    """
    Builds the compiled StateGraph.
    
    Args:
        llm: Language model instance
        tools: List of LangChain tools
        prompt: Chat prompt template
        model_provider: Provider name (e.g., 'gemini', 'bedrock') to determine tool node type
    """
    workflow = StateGraph(AgentState)

    # 1. Define Logic (Inner Function to capture scope)
    async def agent_node(state: AgentState, config: RunnableConfig):
        """
        The main agent node that calls the LLM.
        Captured dependencies: llm, tools, prompt
        """
        logger.info(f"agent_node: Entering with {len(state['messages'])} messages")
        
        # Check if previous message was from 'search_tools' and update available tools if so
        # This requires the agent to have access to the registry, which we will inject via 'tools' context or similar.
        # For now, we assume 'tools' passed to this function are the *initial* tools.
        # To support dynamic tools, we'd need to store them in State or fetch from Registry here.
        
        # Extended logic for Dynamic Tool Binding:
        # If we have a tool registry in config/kwargs (we need to pass it), we can use it.
        # Let's assume we bind the tools passed in.
        
        # Check for tool_registry in config
        tool_registry = config.get("configurable", {}).get("tool_registry")
        current_tools = list(tools) # Copy initial tools
        
        if tool_registry:
            # Check if last message was a tool output from "search_tools"
            last_msg = state["messages"][-1]
            if isinstance(last_msg, ToolMessage) and last_msg.name == "search_tools":
                 # Parse the output to get tool names
                 try:
                     import json
                     # The output is a list of dicts: [{"name":...}, ...]
                     # But it might be varying format depending on LLM.
                     # The tool returns a list of dicts.
                     found_tools_data = json.loads(last_msg.content)
                     if isinstance(found_tools_data, list):
                         for t_data in found_tools_data:
                             t_name = t_data.get("name")
                             t_inst = tool_registry.get_tool(t_name)
                             if t_inst:
                                 current_tools.append(t_inst)
                         logger.info(f"Dynamically added tools: {[t.name for t in current_tools if t not in tools]}")
                 except Exception as e:
                     logger.error(f"Failed to parse search_tools output: {e}")

        # Bind tools to LLM
        # Add search_tools if not present and registry is available? 
        # Actually search_tools should be in the initial 'tools' list if enabled.
        
        logger.info(f"agent_node: Binding {len(current_tools)} tools to LLM...")
        llm_with_tools = llm.bind_tools(current_tools)
        
        # Run chain
        chain = prompt | llm_with_tools
        response = await chain.ainvoke(state)
        
        logger.info(f"agent_node: Got response type={type(response).__name__}")
        if hasattr(response, 'response_metadata'):
            logger.info(f"agent_node: Response Metadata: {response.response_metadata}")
        if hasattr(response, 'content'):
            logger.info(f"agent_node: Content: '{response.content}'")
        
        logger.info(f"agent_node: Tool calls: {len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0}")
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"agent_node: Tool calls details: {[tc['name'] for tc in response.tool_calls]}")
        
        return {"messages": [response]}

    # --- Custom Filtered ToolNode for Partial Execution ---
    class FilteredToolNode:
        """
        A ToolNode that skips tool calls which already have a ToolMessage response.
        This allows partial execution: denied tools have error responses injected,
        and this node only executes the remaining approved tools.
        """
        def __init__(self, tools_list):
            from langgraph.prebuilt import ToolNode
            self._inner_tool_node = ToolNode(tools_list)
            self._tools_by_name = {t.name: t for t in tools_list}
            
        async def __call__(self, state: AgentState, config: RunnableConfig = None):
            messages = state.get("messages", [])
            if not messages:
                return {}
            
            # Find the last AIMessage with tool calls
            ai_message = None
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    ai_message = msg
                    break
            
            if not ai_message:
                return {}
            
            # Collect tool_call_ids that already have responses
            existing_responses = set()
            for msg in messages:
                if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                    existing_responses.add(msg.tool_call_id)
            
            # Execute only tools without responses
            new_messages = []
            for tool_call in ai_message.tool_calls:
                tool_id = tool_call.get("id", "")
                tool_name = tool_call["name"]
                
                if tool_id in existing_responses:
                    logger.info(f"FilteredToolNode: Skipping {tool_name} (already has response)")
                    continue
                
                # Execute the tool
                tool = self._tools_by_name.get(tool_name)
                if tool:
                    try:
                        logger.info(f"FilteredToolNode: Executing {tool_name}")
                        result = await tool.ainvoke(tool_call.get("args", {}))
                        new_messages.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_id,
                                name=tool_name
                            )
                        )
                    except Exception as e:
                        logger.error(f"FilteredToolNode: Error executing {tool_name}: {e}")
                        new_messages.append(
                            ToolMessage(
                                content=f"Error executing tool: {str(e)}",
                                tool_call_id=tool_id,
                                name=tool_name
                            )
                        )
                else:
                    logger.warning(f"FilteredToolNode: Tool {tool_name} not found")
                    new_messages.append(
                        ToolMessage(
                            content=f"Error: Tool '{tool_name}' not found",
                            tool_call_id=tool_id,
                            name=tool_name
                        )
                    )
            
            return {"messages": new_messages} if new_messages else {}

    # 1. Add Nodes
    workflow.add_node("agent", agent_node)
    
    # Use FilteredToolNode instead of standard ToolNode
    workflow.add_node("tools", FilteredToolNode(tools))
    
    workflow.add_node("human_review", human_review_node)

    # 2. Add Edges
    workflow.set_entry_point("agent")
    
    # Conditional edge from agent
    workflow.add_conditional_edges(
        "agent",
        route_tools,
        {
            "tools": "tools",
            "human_review": "human_review",
            END: END
        }
    )

    # From tools, go back to agent
    workflow.add_edge("tools", "agent")
    
    # From human_review, always proceed to tools.
    # FilteredToolNode will skip denied tools (which already have ToolMessage responses)
    # and only execute approved ones. If ALL are denied, it returns empty and agent continues.
    def route_after_human_review(state: AgentState) -> str:
        # Always route to tools - FilteredToolNode handles partial execution
        logger.info("route_after_human_review: Proceeding to filtered tool execution")
        return "tools"
    
    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "tools": "tools"
        }
    )

    # 3. Return uncompiled graph
    # We return the StateGraph so the caller (langchain_agent.py) can compile it 
    # with their preferred checkpointer and interrupt settings.
    return workflow

# --- Wrapper for Legacy Compatibility ---

class GraphAgentExecutor:
    """
    Wraps the compiled graph to mimic the AgentExecutor interface
    used by the rest of the application.
    """
    def __init__(self, graph, checkpointer=None, thread_id="default", tool_registry=None):
        self.graph = graph
        self.checkpointer = checkpointer
        self.thread_id = thread_id
        self.tool_registry = tool_registry
        
    async def invoke(self, input_dict: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Mimics AgentExecutor.invoke
        """
        # Prepare input for graph
        # input_dict usually has {"input": "user query", "chat_history": [...]}
        logger.info("--- Executing via LangGraph Agent ---")
        
        # We need to constructing the initial state
        initial_messages = []
        if "chat_history" in input_dict:
            initial_messages.extend(input_dict["chat_history"])
        
        if "input" in input_dict:
            initial_messages.append(("user", input_dict["input"]))
            
        # Merge config
        run_config = config or {}
        if "configurable" not in run_config:
            run_config["configurable"] = {}
        
        # Ensure thread_id is present for persistence
        if "thread_id" not in run_config["configurable"]:
            run_config["configurable"]["thread_id"] = self.thread_id
            
        # Inject tool_registry if available
        if self.tool_registry:
            run_config["configurable"]["tool_registry"] = self.tool_registry
            
        # Invoke graph
        # Note: This is a synchronous-looking call but valid for async usage if awaited?
        # graph.ainvoke is what we want.
        
        # KEY FIX: If we are resuming (empty messages), pass None to allow clean resume
        graph_input = {"messages": initial_messages} if initial_messages else None
        
        final_state = await self.graph.ainvoke(
            graph_input,
            run_config
        )
        
        # Extract output
        messages = final_state["messages"]
        last_msg = messages[-1]
        output_text = last_msg.content if last_msg else ""
        
        return {"output": output_text}

    async def astream_events(self, input_dict: Dict[str, Any], version: str = "v1", config: Optional[RunnableConfig] = None):
        """
        Mimics AgentExecutor.astream_events.
        LangGraph supports astream_events directly.
        """
        # Prepare input for graph
        initial_messages = []
        if "chat_history" in input_dict:
            initial_messages.extend(input_dict["chat_history"])
        
        if "input" in input_dict:
            initial_messages.append(("user", input_dict["input"]))
            
        # Merge config
        run_config = config or {}
        if "configurable" not in run_config:
            run_config["configurable"] = {}
        
        if "thread_id" not in run_config["configurable"]:
            run_config["configurable"]["thread_id"] = self.thread_id
            
        # Inject tool_registry if available
        if self.tool_registry:
            run_config["configurable"]["tool_registry"] = self.tool_registry
            
        logger.info("--- Executing via LangGraph Agent (Streaming) ---")
        
        # KEY FIX: If we are resuming (empty messages), pass None to allow clean resume
        graph_input = {"messages": initial_messages} if initial_messages else None
        
        # Delegate to graph
        async for event in self.graph.astream_events(
            graph_input,
            run_config,
            version=version
        ):
            yield event
