import logging
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
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        denied_tools = []
        approved_tools = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_id = tool_call.get("id", "")
            
            # Find the pending approval for this tool
            for pid, data in list(PendingApproval._pending.items()):
                if data['user_id'] == user_id and data['tool_name'] == tool_name:
                    if data['approved'] is False:
                        denied_tools.append((tool_name, tool_id, pid))
                        # Clean up the denied approval
                        PendingApproval.remove(pid)
                    elif data['approved'] is True:
                        approved_tools.append((tool_name, tool_id, pid))
                        # Keep approved ones for tool execution, clean up after
                    break
        
        # If any tools were denied, inject ToolMessage with error
        if denied_tools:
            new_messages = []
            for tool_name, tool_id, pid in denied_tools:
                logger.info(f"Tool {tool_name} was DENIED by user")
                # Create a fake ToolMessage response indicating denial
                new_messages.append(
                    ToolMessage(
                        content=f"Error: User denied permission to execute tool '{tool_name}'. Do not retry this tool.",
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
            
            # Return these messages to append to state, causing agent to see denial
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
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                # The tool name might be 'server_tool', we need to check effectively.
                # Our check_tool_approval mainly needs the tool name suffix if generic, 
                # but let's pass the full name.
                # Note: tools.py constructs names as "ServerName_ToolName".
                
                # We strip the Unique ID prefix if we want to check the raw name? 
                # Currently check_tool_approval takes 'tool_name'. 
                # Let's assume the permission system handles the unique name or we parse it.
                # For now, pass the full unique name.
                
                # Check approval status
                needs_approval, approval_type = await check_tool_approval(db, user_id, tool_name)
                
                if needs_approval and approval_type != 'always':
                    requires_approval = True
                    
                    # CRITICAL FIX: Create the PendingApproval record so the API/Frontend knows to ask the user.
                    # Without this, the graph pauses, but the user receives no notification.
                    approval_id = PendingApproval.create(
                        user_id=user_id,
                        tool_name=tool_name,
                        server_name="unknown", # Server name resolution would require extra mapping
                        tool_input=tool_call.get('args', {})
                    )
                    logger.info(f"Blocking tool {tool_name} for approval. Created PendingApproval ID: {approval_id}")
                    
                    # We can break early if we just want to stop at the first roadblock
                    # logic-wise, we need to approve 'all' or 'one by one'.
                    # The current flow pauses execution completely, so valid to stop here.
                    break
    
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
        
        # Bind tools to LLM
        logger.info(f"agent_node: Binding {len(tools)} tools to LLM: {[t.name for t in tools[:3]]}...")
        llm_with_tools = llm.bind_tools(tools)
        
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

    # 1. Add Nodes
    workflow.add_node("agent", agent_node)
    
    # Standard ToolNode
    workflow.add_node("tools", ToolNode(tools))
    
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
    
    # From human_review, conditionally route based on approval status
    # If denied tools, they added ToolMessage, so go back to agent to process
    # If approved, proceed to tools
    def route_after_human_review(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "tools"
        
        # Check if the last message is a ToolMessage (denial case)
        last_msg = messages[-1]
        if hasattr(last_msg, "type") and last_msg.type == "tool":
            # Tool denial message was added, go to agent to process
            return "agent"
        
        # Otherwise, proceed to tools (approved case)
        return "tools"
    
    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "tools": "tools",
            "agent": "agent"
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
    def __init__(self, graph, checkpointer=None, thread_id="default"):
        self.graph = graph
        self.checkpointer = checkpointer
        self.thread_id = thread_id
        
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
