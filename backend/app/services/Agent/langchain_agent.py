# import os
# import json # NEW: Needed for JSON serialization for SSE data
# import asyncio
# from typing import Any, AsyncGenerator # NEW: AsyncGenerator for SSE

# # --- NEW IMPORTS FOR RAG ---
# from langchain_core.tools import tool
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from .rag_setup import setup_rag_retriever # Assuming you have rag_setup.py with the Pinecone code

# # --- EXISTING IMPORTS ---
# from langchain_core.runnables import RunnableLambda
# from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.messages import SystemMessage, AIMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.agents import create_tool_calling_agent, AgentExecutor
# from langchain.tools import StructuredTool
# from pydantic import create_model
# from langchain_community.chat_message_histories import RedisChatMessageHistory
# from .mcp_connector import MCPConnector
# from .config import MCP_SERVERS

# # --- NEW: FastAPI Imports for SSE ---
# from fastapi import APIRouter, Depends, HTTPException, Request # Added Request
# from sse_starlette.sse import EventSourceResponse # NEW: For SSE streaming
# from pydantic import BaseModel
# import uuid
# import logging # NEW: For better logging

# # Setup basic logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# # Global instance for the agent pipeline (initialized once)
# agent_executor_instance = None # Renamed to reflect it's now AgentExecutor

# class AskRequest(BaseModel): # Minimal Request model
#     prompt: str
#     session_id: str = None

# async def get_agent_from_state() -> AgentExecutor: # Type hint changed
#     global agent_executor_instance
#     if agent_executor_instance is None:
#         logger.info("Initializing AgentExecutor...")
#         agent_executor_instance = await create_final_agent_pipeline()
#         logger.info("AgentExecutor initialized.")
#     return agent_executor_instance

# # --- STEP 1: DEFINE THE PROMPTS (AGENT PROMPT IS UNCHANGED) ---

# def build_agent_prompt():
#     """
#     MODIFIED: Builds a prompt for an agent that knows how to use
#     both specific tools and a general knowledge base.
#     """
#     # THE PROMPT IS UPDATED HERE TO GUIDE THE AGENT'S TOOL CHOICE
#     system_prompt = (
#         "You are an expert assistant. Your goal is to answer a user's question accurately and concisely.\n"
#         "You have access to a set of specialized tools for specific, structured tasks (like checking a server status).\n"
#         "You ALSO have access to a general knowledge base via the `search_knowledge_base` tool.\n\n"
#         "Follow these rules for choosing a tool:\n"
#         "1. First, check if the user's question can be directly answered by one of the specialized tools. If it's a clear match, use that tool.\n"
#         "2. If the question is more general, open-ended, or asks about policies, conventions, or information not covered by the specialized tools, you MUST use the `search_knowledge_base` tool.\n"
#         "3. After using a tool, provide the answer clearly in plain text."
#     )
#     return ChatPromptTemplate.from_messages([
#         SystemMessage(content=system_prompt),
#         MessagesPlaceholder(variable_name="chat_history"),
#         ("user", "{input}"),
#         MessagesPlaceholder(variable_name="agent_scratchpad"),
#     ])

# def build_formatter_prompt():
#     """
#     Builds a prompt for a presentation layer. (UNCHANGED)
#     """
#     system_prompt = (
#         "You are an expert web designer. Your task is to convert a user's original question and a plain-text answer "
#         "into a clean, professional HTML snippet. Use tables for structured data, <h3> for titles, "
#         "and <b> for emphasis. Do not add any new information or change the facts, only format the provided text."
#     )
#     return ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         ("user", "Original Question: {question}\n\nPlain Text Answer:\n{answer}")
#     ])


# # --- STEP 2: YOUR TOOL-BUILDING LOGIC (UNCHANGED) ---

# def create_tool_func(tool_name: str, connector, pydantic_model=None):
#     # This function is unchanged
#     async def async_func(**kwargs):
#         if pydantic_model:
#             try:
#                 kwargs = pydantic_model(**kwargs).dict()
#             except Exception as e:
#                 return f"Invalid input arguments: {e}"
#         result = await connector.run_tool(tool_name, kwargs)
#         return result

#     def sync_func(**kwargs):
#         if not pydantic_model and len(kwargs) == 1 and "input_str" in kwargs:
#             try:
#                 kwargs = json.loads(kwargs["input_str"])
#             except json.JSONDecodeError:
#                 return "Input must be valid JSON string representing tool parameters."
#         try:
#             loop = asyncio.get_event_loop()
#         except RuntimeError:
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#         return loop.run_until_complete(async_func(**kwargs))
#     return sync_func, async_func

# async def build_tools_from_servers():
#     # This function is unchanged
#     built_tools = []
#     for server_name, url in MCP_SERVERS.items():
#         connector = MCPConnector(url)
#         tools_data = await connector.list_tools()
#         for tool_info in tools_data:
#             tool_name = tool_info.get("name")
#             description = tool_info.get("description")
#             input_schema = tool_info.get("argument_schema")
#             pydantic_model = None
#             if input_schema and input_schema.get("type") == "object":
#                 try:
#                     properties = input_schema.get("properties", {})
#                     required_fields = input_schema.get("required", [])
#                     fields = {prop_name: (
#                         {
#                             "string": str, "integer": int, "number": float, "boolean": bool
#                         }.get(prop_info.get("type", "string"), str),
#                         ... if prop_name in required_fields else None
#                     ) for prop_name, prop_info in properties.items()}
#                     model_name = input_schema.get("title") or f"{tool_name}Args"
#                     pydantic_model = create_model(model_name, **fields)
#                 except Exception as e:
#                     logger.error(f"Error creating Pydantic model for tool {tool_name}: {e}")
#             sync_func, async_func = create_tool_func(tool_name, connector, pydantic_model)
#             tool = StructuredTool.from_function(
#                 func=sync_func, coroutine=async_func, name=tool_name,
#                 description=description, args_schema=pydantic_model,
#             )
#             built_tools.append(tool)
#     return built_tools


# # --- STEP 3: MEMORY MANAGEMENT (UNCHANGED) ---

# def get_session_memory(session_id: str) -> RedisChatMessageHistory:
#     """Creates a Redis-backed memory object for a given session_id."""
#     redis_url = os.getenv("REDIS_URL_MEMORY", "redis://localhost:6379/1")
#     logger.info(f"Attempting to get Redis memory for session {session_id} at URL: {redis_url}")
#     try:
#         # This is where the actual connection to Redis is attempted.
#         # If Redis is not running or inaccessible, an exception will be raised here.
#         history = RedisChatMessageHistory(session_id=session_id, url=redis_url)
#         logger.info(f"Successfully initialized RedisChatMessageHistory for session {session_id}.")
#         return history
#     except Exception as e:
#         logger.error(f"Failed to initialize RedisChatMessageHistory for session {session_id}. Error: {e}", exc_info=True)
#         # Return None if memory initialization fails so the caller can handle it.
#         return None 


# # --- STEP 4: THE ROBUST PIPELINE FACTORY (MODIFIED FOR SSE INTEGRATION) ---

# async def create_final_agent_pipeline() -> AgentExecutor: # MODIFIED RETURN TYPE
#     """
#     MODIFIED: This factory builds the core AgentExecutor.
#     Streaming logic and memory management will be handled directly in the FastAPI endpoint.
#     """
#     # Part 1: Initialize LLM and our new RAG retriever
#     llm = ChatGoogleGenerativeAI(
#         model="gemini-1.5-flash",
#         google_api_key=os.getenv("GOOGLE_API_KEY"),
#         temperature=0
#     )
#     # NEW: Setup the RAG retriever by calling our function from rag_setup.py
#     rag_retriever = setup_rag_retriever()

#     # Part 2: NEW - Create the RAG Search Tool
#     rag_prompt = ChatPromptTemplate.from_template(
#         "Answer the user's question based only on the following context:\n\n{context}\n\nQuestion: {input}"
#     )
#     document_chain = create_stuff_documents_chain(llm, rag_prompt)
    
#     @tool
#     async def search_knowledge_base(input: str) -> str:
#         """
#         Searches the company's knowledge base for answers to general questions, 
#         policies, or other unstructured information. Use this when no other
#         specialized tool is suitable.
#         """
#         logger.info(f"Using search_knowledge_base for: {input}")
#         retrieved_docs = await rag_retriever.ainvoke(input)
#         response = await document_chain.ainvoke({
#             "input": input,
#             "context": retrieved_docs
#         })
#         return response

#     # Part 3: MODIFIED - Build the full tool list
#     specialized_tools = await build_tools_from_servers()
#     tools = specialized_tools + [search_knowledge_base] # Add our new RAG tool

#     # Part 4: Create agent
#     agent_prompt = build_agent_prompt() 
#     agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=agent_prompt)
#     agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

#     # REMOVED: run_agent_and_format, final_chain, agent_with_memory
#     # These are now handled directly in the SSE endpoint.
    
#     return agent_executor # MODIFIED: Return the core AgentExecutor
import os
import json
import asyncio
from typing import Any, AsyncGenerator, Dict, List
from functools import lru_cache

# --- LangChain Imports ---
from langchain_core.tools import tool
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import StructuredTool

# --- Pydantic Imports ---
from pydantic import create_model, BaseModel, Field

from langchain_community.chat_message_histories import RedisChatMessageHistory

# --- Your Project's Local Imports ---
from .rag_setup import setup_rag_retriever
from .mcp_connector import MCPConnector

import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- STEP 1: DEFINE THE PROMPTS (Unchanged) ---

def build_agent_prompt():
    """
    Builds a prompt for an agent that knows how to use
    both specific tools and a general knowledge base.
    """
    system_prompt = (
        "You are an expert assistant. Your goal is to answer a user's question accurately and concisely.\n"
        "You have access to a set of specialized tools for specific, structured tasks (like checking a server status).\n"
        "You ALSO have access to a general knowledge base via the `search_knowledge_base` tool.\n\n"
        "Follow these rules for choosing a tool:\n"
        "1. First, check if the user's question can be directly answered by one of the specialized tools. If it's a clear match, use that tool.\n"
        "2. If the question is more general, open-ended, or asks about policies, conventions, or information not covered by the specialized tools, you MUST use the `search_knowledge_base` tool.\n"
        
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
        "You are an expert web designer. Your task is to convert a user's original question and a plain-text answer "
        "into a clean, professional HTML snippet. Use tables for structured data, <h3> for titles, "
        "and <b> for emphasis. Do not add any new information or change the facts, only format the provided text."
    )
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Original Question: {question}\n\nPlain Text Answer:\n{answer}")
    ])


# --- STEP 2: TOOL-BUILDING LOGIC ---

def create_tool_func(tool_name: str, connector, pydantic_model=None):
    """
    Creates the asynchronous and synchronous functions that the LangChain tool will wrap.
    The `pydantic_model` argument is for context but isn't used here, as the validation
    happens before this function is ever called.
    """
    async def async_func(**kwargs):
        # kwargs will be a validated dictionary of arguments from the tool call
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

async def build_tools_from_servers(user_mcp_servers: Dict[str, str]) -> List[StructuredTool]:
    """
    Builds LangChain tools from a user-specific server dictionary.
    This function is now called on every request with the current user's data.
    """
    built_tools = []
    for server_name, url in user_mcp_servers.items():
        try:
            connector = MCPConnector(url)
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
                            python_type = {
                                "string": str, "integer": int, "number": float, "boolean": bool
                            }.get(prop_type_str, str)
                            
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

                sync_func, async_func = create_tool_func(tool_name, connector, pydantic_model)
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

@lru_cache(maxsize=None)
def get_llm():
    """Returns a cached instance of the LLM."""
    logger.info("--- Creating new ChatGoogleGenerativeAI instance (should happen only once per worker) ---")
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

@lru_cache(maxsize=None)
def get_knowledge_tool():
    """Returns a cached instance of the RAG-based knowledge tool."""
    logger.info("--- Creating new RAG knowledge tool (should happen only once per worker) ---")
    llm = get_llm()
    rag_retriever = setup_rag_retriever()
    rag_prompt = ChatPromptTemplate.from_template(
        "Answer the user's question based only on the following context:\n\n{context}\n\nQuestion: {input}"
    )
    document_chain = create_stuff_documents_chain(llm, rag_prompt)
    
    @tool
    async def search_knowledge_base(input: str) -> str:
        """
        Searches the company's knowledge base for answers to general questions, 
        policies, or other unstructured information. Use this when no other
        specialized tool is suitable.
        """
        logger.info(f"Using search_knowledge_base for: {input}")
        retrieved_docs = await rag_retriever.ainvoke(input)
        response = await document_chain.ainvoke({
            "input": input,
            "context": retrieved_docs
        })
        return response
    return search_knowledge_base

async def create_final_agent_pipeline(user_mcp_servers: Dict[str, str]) -> AgentExecutor:
    """
    Creates a user-specific AgentExecutor pipeline on-demand.
    It reuses cached components (LLM, RAG tool) and builds fresh user-specific tools.
    """
    llm = get_llm()
    knowledge_tool = get_knowledge_tool()

    specialized_tools = await build_tools_from_servers(user_mcp_servers)
    
    all_tools = specialized_tools + [knowledge_tool]
    logger.info(f"Agent created with {len(all_tools)} tools: {[t.name for t in all_tools]}")

    agent_prompt = build_agent_prompt()
    agent = create_tool_calling_agent(llm=llm, tools=all_tools, prompt=agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)
    
    return agent_executor