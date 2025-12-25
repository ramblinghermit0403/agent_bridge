
import os
import json
import asyncio
from typing import Any, AsyncGenerator, Dict, List
from functools import lru_cache

# --- LangChain Imports ---
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, create_react_agent, AgentExecutor
from langchain.tools import StructuredTool

# --- Pydantic Imports ---
from pydantic import create_model, BaseModel, Field

from langchain_community.chat_message_histories import RedisChatMessageHistory

# --- Your Project's Local Imports ---
from .mcp_connector import MCPConnector

import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- MONKEYPATCH: Fix for Gemini 2.5 Flash 'finish_reason' int crash ---
# The installed version of langchain-google-genai expects finish_reason to be an enum with .name,
# but Gemini 2.5 Flash sometimes returns an int (e.g. 12). This patch handles both.
import langchain_google_genai.chat_models
from typing import Any, List, Optional, cast, Dict
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain.tools.render import render_text_description

# Conditionally import UsageMetadata and subtract_usage
try:
    from langchain_core.messages import UsageMetadata
except ImportError:
    # Fallback for older langchain-core versions
    from typing import TypedDict
    class UsageMetadata(TypedDict, total=False):
        input_tokens: int
        output_tokens: int
        total_tokens: int
        input_token_details: Dict[str, Any]
        output_token_details: Dict[str, Any]

try:
    from langchain_core.messages.ai import subtract_usage
except ImportError:
    # Fallback: simple subtraction if available, else return current
    def subtract_usage(current: UsageMetadata, previous: UsageMetadata) -> UsageMetadata:
        # Simplified fallback that doesn't actually subtract if complicated logic is needed
        # But preventing crash is key.
        return current

try:
    _parse_response_candidate = langchain_google_genai.chat_models._parse_response_candidate
except AttributeError:
    # Fallback if the internal function isn't found (shouldn't happen on standard install)
    logger.warning("Could not find _parse_response_candidate, monkeypatch might fail.")
    # We might need to define a dummy or stop. But preventing crash is priority.
    def _parse_response_candidate(*args, **kwargs):
        return AIMessage(content="")

def _patched_response_to_result(
    response: Any,
    stream: bool = False,
    prev_usage: Optional[UsageMetadata] = None,
) -> ChatResult:
    """Patched version of _response_to_result to handle int finish_reason."""
    llm_output = (
        {"prompt_feedback": response.prompt_feedback.model_dump()}
        if response.prompt_feedback
        else {}
    )

    # Get usage metadata
    lc_usage = None
    try:
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            # thoughts_token_count might not be in older PyDantic models, use getattr
            thought_tokens = getattr(response.usage_metadata, "thoughts_token_count", 0) or 0
            
            candidates_tokens = response.usage_metadata.candidates_token_count or 0
            output_tokens = candidates_tokens + thought_tokens
            total_tokens = response.usage_metadata.total_token_count or 0
            
            # cached_content_token_count might also be missing
            cache_read_tokens = getattr(response.usage_metadata, "cached_content_token_count", 0) or 0
            
            if input_tokens + output_tokens + cache_read_tokens + total_tokens > 0:
                cumulative_usage = UsageMetadata(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    input_token_details={"cache_read": cache_read_tokens} if cache_read_tokens else {},
                )
                if thought_tokens > 0:
                     # Add reasoning details if supported by installed langchain-core (might not be available in old versions)
                     # We skip adding to 'output_token_details' to be safe with old versions, 
                     # unless we check if it supports it.
                     pass 

                # previous usage metadata needs to be subtracted
                lc_usage = subtract_usage(cumulative_usage, prev_usage) if prev_usage else cumulative_usage
    except Exception as e:
        # If usage tracking fails, just ignore it rather than crashing
        # logger.warning(f"Failed to process usage metadata: {e}")
        lc_usage = None

    generations: List[ChatGeneration] = []

    for candidate in response.candidates or []:
        generation_info: dict[str, Any] = {}
        
        # --- FIX IS HERE ---
        if candidate.finish_reason:
            if hasattr(candidate.finish_reason, "name"):
                generation_info["finish_reason"] = candidate.finish_reason.name
            else:
                # Handle int or other types safely
                generation_info["finish_reason"] = str(candidate.finish_reason)
        # -------------------

        generation_info["safety_ratings"] = (
            [safety_rating.model_dump() for safety_rating in candidate.safety_ratings]
            if candidate.safety_ratings
            else []
        )

        try:
            message = _parse_response_candidate(
                candidate,
                streaming=stream,
                model_name=response.model_version if hasattr(response, "model_version") else None,
                model_name_for_content=response.model_version if hasattr(response, "model_version") else None,
            )
        except TypeError:
            # Fallback for older versions that don't accept model_name/model_name_for_content
            # This handles the specific error: unexpected keyword argument 'model_name'
            message = _parse_response_candidate(
                candidate,
                streaming=stream,
            )

        # Ensure response_metadata exists
        if not hasattr(message, "response_metadata"):
            message.response_metadata = {}
        
        # Add generation info to metadata
        message.response_metadata.update(generation_info)
        
        # Attach usage
        message.usage_metadata = lc_usage

        if stream:
            generations.append(
                ChatGenerationChunk(
                    message=cast(AIMessageChunk, message),
                    generation_info=generation_info,
                )
            )
        else:
            generations.append(
                ChatGeneration(message=message, generation_info=generation_info)
            )

    if not response.candidates:
        # Handle empty response (e.g. safety block)
        if stream:
            generations = [
                ChatGenerationChunk(
                    message=AIMessageChunk(content=""),
                    generation_info={},
                )
            ]
        else:
            generations = [ChatGeneration(message=AIMessage(content=""), generation_info={})]

    return ChatResult(generations=generations, llm_output=llm_output)

# Apply the patch
langchain_google_genai.chat_models._response_to_result = _patched_response_to_result
logger.info("Monkeypatched langchain_google_genai.chat_models._response_to_result for Gemini 2.5 compatibility.")




# --- STEP 1: DEFINE THE PROMPTS (Unchanged) ---

def build_agent_prompt(model_provider: str = "gemini"):
    """
    Builds a prompt for an agent that knows how to use
    both specific tools and a general knowledge base.
    """
    # Universal system prompt for all models
    system_prompt = (
        "You are an expert assistant. Your goal is to answer a user's question accurately and concisely.\n"
        "You have access to a set of specialized tools for specific, structured tasks (like checking a server status).\n"
        "You ALSO have access to a general knowledge base via the `search_knowledge_base` tool.\n\n"
        "Follow these rules for choosing a tool:\n"
        "1. First, check if the user's question can be directly answered by one of the specialized tools. If it's a clear match, use that tool.\n"
        # "2. If the question is more general, open-ended, or asks about policies, conventions, or information not covered by the specialized tools, you MUST use the `search_knowledge_base` tool.\n"
        
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

def build_formatter_prompt():
    """
    Builds a prompt for a presentation layer.
    """
    system_prompt = (
        "You are a frontend implementation expert. Your task is to format the answer as clean, semantic HTML "
        "to be rendered inside a chat bubble. \n"
        "RULES:\n"
        "1. DO NOT use <html>, <head>, <body>, or <!DOCTYPE> tags.\n"
        "2. DO NOT use inline `style` attributes. The frontend handles styling.\n"
        "3. Use only standard tags: <p>, <ul>, <ol>, <li>, <strong>, <em>, <br>, <table>, <thead>, <tbody>, <tr>, <th>, <td>.\n"
        "4. Start directly with the content (e.g., <p>Answer...</p>).\n"
        "5. For code blocks, use <pre><code>...</code></pre>.\n"
        "6. Do not add any new facts, strictly format the provided text."
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        ("user", "Question: {question}\nAnswer: {answer}\nFormat this answer as HTML:"),
    ]) 

def build_react_prompt():
    """
    Builds a ReAct-style prompt for models that don't support native tool calling well.
    """
    system_prompt = (
        "You are an expert assistant. Answer the following questions as best you can. "
        "You are designed to solving tasks using a specific Reason+Act (ReAct) process.\n\n"
        
        "You have access to the following tools:\n\n"
        "{tools}\n\n"
        
        "Use the following format strictly:\n\n"
        "Question: the input question you must answer\n"
        "Thought: you should always think about what to do\n"
        "Action: the action to take, should be one of [{tool_names}]\n"
        "Action Input: the input to the action (must be a valid string or JSON)\n"
        "Observation: the result of the action\n"
        "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
        "Thought: I now know the final answer\n"
        "Final Answer: the final answer to the original input question\n\n"
        
        "IMPORTANT RULES:\n"
        "1. You MUST use the exact headers: 'Thought:', 'Action:', 'Action Input:'. Do NOT bold them or change case.\n"
        "2. The 'Action' must be the EXACT name of a tool from the list.\n"
        "3. 'Action Input' MUST be a JSON object `{\"arg\": \"value\"}`. Do NOT send a plain string unless the tool takes exactly one argument.\n"
        "4. Output 'Observation:' ONLY if you are simulating a result (you usually wait for the system to provide it).\n"
        "5. If you receive an 'Invalid Format' observation, it means you forgot the 'Action:' or 'Action Input:' header. Retry immediately with correct formatting.\n"
        "6. Ensure there is a newline before 'Observation:'.\n\n"
        
        "EXAMPLE:\n"
        "Question: Check weather in SF\n"
        "Thought: I need to use check_weather.\n"
        "Action: check_weather\n"
        "Action Input: {\"location\": \"San Francisco\"}\n"
        "Observation: Sunny, 22C\n"
        "Thought: It is sunny.\n"
        "Final Answer: Sunny, 22C\n\n"
        
        "Begin!"
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}\n\n{agent_scratchpad}"),
    ]) 

# ... (omitted)

# Duplicate create_final_agent_pipeline removed to use the correct implementation below



# --- STEP 2: TOOL-BUILDING LOGIC ---

def create_tool_func(tool_name: str, connector, pydantic_model=None, user_id: str=None, unique_tool_name: str=None):
    """
    Creates the asynchronous and synchronous functions that the LangChain tool will wrap.
    Includes permission checking logic.
    """
    async def async_func(*args, **kwargs):
        # Handle positional argument if passed (sometimes happens with single-input tools)
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                kwargs.update(args[0])
            elif len(args) == 1 and isinstance(args[0], str):
                 # Try to parse string as JSON if it looks like a dict
                 import json
                 arg_str = args[0].strip()
                 if arg_str.startswith("{") and arg_str.endswith("}"):
                     try:
                         parsed_kwargs = json.loads(arg_str)
                         if isinstance(parsed_kwargs, dict):
                             kwargs.update(parsed_kwargs)
                     except json.JSONDecodeError:
                         pass # Not valid JSON, treat as standard string arg
        
        # 1. Check permissions if user_id is provided
        if user_id:
            from app.services.tool_permissions_helper import check_tool_approval, PendingApproval
            from sqlalchemy.ext.asyncio import AsyncSession
            
            # Create a fresh async session for the check
            # We can't reuse the request dependency session here easily as it's not passed down
            # But we can create a new one.
            from app.database.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                needs_approval, approval_type = await check_tool_approval(db, user_id, tool_name)
                
                if needs_approval and approval_type != 'always':
                    # Logic to block and wait for approval
                    # Use unique_tool_name for PendingApproval SO THAT agent.py can find it (it sees unique name in event)
                    approval_name = unique_tool_name if unique_tool_name else tool_name
                    
                    approval_id = PendingApproval.create(
                        user_id=user_id,
                        tool_name=approval_name, 
                        server_name="unknown", # We can improve this later
                        tool_input=kwargs
                    )
                    
                    logger.info(f"Blocking tool {approval_name} (raw: {tool_name}) for approval {approval_id}")
                    
                    try:
                        # Wait for approval
                        approved = False
                        for _ in range(60): # 60 seconds timeout
                            await asyncio.sleep(1)
                            pending = PendingApproval.get(approval_id)
                            # Check if approved changed from None to True/False
                            if pending and pending['approved'] is not None:
                                approved = pending['approved']
                                break
                        
                        if not approved:
                            raise ToolException(f"Tool execution denied for {tool_name}")
                    finally:
                        PendingApproval.remove(approval_id)

        # 2. Execute tool
        return await connector.run_tool(tool_name, kwargs)
    
    def sync_func(**kwargs):
        # This is a fallback, primarily for non-async agents.
        # It's better to use the async tool directly.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_func(**kwargs))
        
    return sync_func, async_func

class ToolException(Exception):
    pass

async def build_tools_from_servers(user_mcp_servers: Dict[str, Dict[str, Any]], user_id: str = None) -> List[StructuredTool]:
    """
    Builds LangChain tools from a user-specific server dictionary.
    This function is now called on every request with the current user's data.
    """
    built_tools = []
    for server_name, server_info in user_mcp_servers.items():
        try:
            # Handle both old/simple format (str) and new format (dict) for safety
            if isinstance(server_info, str):
                url = server_info
                creds = None
            else:
                url = server_info.get("url")
                creds = server_info.get("credentials")

            connector = MCPConnector(url, credentials=creds)
            tools_data = await connector.list_tools()

            for tool_info in tools_data:
                tool_name = tool_info.get("name")
                description = tool_info.get("description", "No description provided.")
                input_schema = tool_info.get("argument_schema")
                pydantic_model = None

                # Create the Pydantic model dynamically from the tool's schema
                if input_schema and input_schema.get("type") == "object" and "properties" in input_schema:
                    try:
                        properties = input_schema.get("properties", {})
                        required_fields = input_schema.get("required", [])
                        
                        fields = {}
                        for prop_name, prop_info in properties.items():
                            prop_type_str = prop_info.get("type", "string")
                            
                            if prop_type_str == "array":
                                python_type = List[Any]
                            elif prop_type_str == "object":
                                python_type = Dict[str, Any]
                            elif prop_type_str == "integer":
                                python_type = int
                            elif prop_type_str == "number":
                                python_type = float
                            elif prop_type_str == "boolean":
                                python_type = bool
                            else:
                                python_type = str
                            
                            field_description = prop_info.get("description", f"The {prop_name} for the tool.")
                            
                            if prop_name in required_fields:
                                fields[prop_name] = (python_type, Field(..., description=field_description))
                            else:
                                fields[prop_name] = (python_type, Field(None, description=field_description))

                        model_name = input_schema.get("title", f"{tool_name.capitalize()}InputModel")
                        pydantic_model = create_model(model_name, **fields)

                    except Exception as e:
                        logger.error(f"Error creating Pydantic model for tool '{tool_name}': {e}", exc_info=True)
                        continue # Skip this tool if its model can't be created
                
                unique_tool_name = f"{server_name.replace(' ', '')}_{tool_name}"
                full_description = f"{description} This tool is from the '{server_name}' server."

                sync_func, async_func = create_tool_func(tool_name, connector, pydantic_model, user_id=user_id, unique_tool_name=unique_tool_name)
                tool_instance = StructuredTool.from_function(
                    func=sync_func, 
                    coroutine=async_func, 
                    name=unique_tool_name,
                    description=full_description,
                    args_schema=pydantic_model, # Pass the dynamically created model here
                )
                built_tools.append(tool_instance)
        except Exception as e:
            logger.error(f"Skipping tools for server '{server_name}' due to connection error: {e}")
            continue
    return built_tools


# --- STEP 3: MEMORY MANAGEMENT (Unchanged) ---

def get_session_memory(session_id: str) -> RedisChatMessageHistory:
    """Creates a Redis-backed memory object for a given session_id."""
    redis_url = os.getenv("REDIS_URL_MEMORY", "redis://localhost:6379/1")
    return RedisChatMessageHistory(session_id=session_id, url=redis_url)


# --- STEP 4: THE ROBUST, PER-REQUEST PIPELINE FACTORY ---

from langchain_aws import ChatBedrockConverse

@lru_cache(maxsize=16) # Reduced maxsize just in case, though clients are small
def get_llm(model_provider: str = "gemini", model_name: str = "gemini-2.5-flash", region_name: str = None):
    """Returns a cached instance of the LLM based on provider."""
    
    # Use configured region if not specified
    if not region_name:
        region_name = os.getenv("AWS_REGION", "us-east-1")
    
    if model_provider == "bedrock":
        logger.info(f"--- Creating ChatBedrockConverse instance: {model_name} in {region_name} ---")
        return ChatBedrockConverse(
            model=model_name,
            region_name=region_name,
            # credentials are auto-loaded from env AWS_ACCESS_KEY_ID etc by boto3
            temperature=0,
            disable_streaming=True # streaming tool calls causing issues with Nova models
        )
    else:
        # Default to Gemini
        logger.info(f"--- Creating ChatGoogleGenerativeAI instance: {model_name} ---")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )


async def create_final_agent_pipeline(
    user_mcp_servers: Dict[str, Any], 
    user_id: str = None,
    model_provider: str = "gemini",
    model_name: str = "gemini-2.5-flash"
) -> AgentExecutor:
    """
    Creates a user-specific AgentExecutor pipeline on-demand.
    It reuses cached components (LLM, RAG tool) and builds fresh user-specific tools.
    """
    llm = get_llm(model_provider, model_name)
    # knowledge_tool = get_knowledge_tool()

    specialized_tools = await build_tools_from_servers(user_mcp_servers, user_id=user_id)
    
    
    all_tools = specialized_tools  # Disabled knowledge base as per user request
    logger.info(f"Agent created with {len(all_tools)} tools: {[t.name for t in all_tools]}")

    # Unified Agent Creation: Use Tool Calling Agent for ALL models.
    # We rely on ChatBedrockConverse with disable_streaming=True for Nova Pro stability.
    agent_prompt = build_agent_prompt(model_provider)
    
    agent = create_tool_calling_agent(llm=llm, tools=all_tools, prompt=agent_prompt)
        
    agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True, handle_parsing_errors=True)
    
    return agent_executor