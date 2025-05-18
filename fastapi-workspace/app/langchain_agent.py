from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from app.mcp_connector import MCPConnector
from app.config import MCP_SERVERS
import asyncio
import json
from langchain.tools import Tool
from pydantic import create_model
import asyncio
from pydantic import create_model
from langchain.tools import StructuredTool, Tool
from typing import Any
import json

def build_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessage(content="You are a helpful agent that uses tools to answer user questions."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])



# def create_tool_func(tool_name: str, connector, pydantic_model=None):
#     """
#     Returns a synchronous function that calls the MCP connector asynchronously.
#     This function will be used as the Tool.func.
#     """
#     # The actual async call to MCP server
#     async def async_call(params: dict):
#         result = await connector.run_tool(tool_name, params)
#         return result

#     if pydantic_model:
#         # If we have a schema, the tool function expects typed args matching the model
#         def tool_func(**kwargs):
#             # Validate and parse arguments with Pydantic
#             try:
#                 validated_args = pydantic_model(**kwargs)
#             except Exception as e:
#                 return f"Invalid input arguments: {e}"

#             # Run async MCP call in event loop (since Tool expects sync func)
#             try:
#                 loop = asyncio.get_event_loop()
#             except RuntimeError:
#                 # no event loop in current thread
#                 loop = asyncio.new_event_loop()
#                 asyncio.set_event_loop(loop)

#             result = loop.run_until_complete(async_call(validated_args.dict()))
#             # Return stringified result for LangChain tool
#             import json
#             return json.dumps(result, indent=2)
#     else:
#         # No schema: accept a raw JSON string as input (or kwargs?)
#         def tool_func(input_str: str):
#             import json
#             try:
#                 params = json.loads(input_str)
#             except json.JSONDecodeError:
#                 return "Input must be a valid JSON string representing tool parameters."

#             try:
#                 loop = asyncio.get_event_loop()
#             except RuntimeError:
#                 loop = asyncio.new_event_loop()
#                 asyncio.set_event_loop(loop)

#             result = loop.run_until_complete(async_call(params))
#             return json.dumps(result, indent=2)

#     return tool_func





# async def build_tools_from_servers():
#     built_tools = []

#     for server_name, url in MCP_SERVERS.items():
#         connector = MCPConnector(url)
#         tools_data = await connector.list_tools()

#         for tool_info in tools_data:
#             tool_name = tool_info.get("name")
#             description = tool_info.get("description")
#             input_schema = tool_info.get("argument_schema")  # ✅ Correct key name

#             pydantic_model = None
#             if input_schema and input_schema.get("type") == "object":
#                 try:
#                     properties = input_schema.get("properties", {})
#                     required_fields = input_schema.get("required", [])
#                     fields = {}

#                     for prop_name, prop_info in properties.items():
#                         json_type = prop_info.get("type", "string")
#                         python_type = str
#                         if json_type == "integer":
#                             python_type = int
#                         elif json_type == "number":
#                             python_type = float
#                         elif json_type == "boolean":
#                             python_type = bool

#                         default = ... if prop_name in required_fields else None
#                         fields[prop_name] = (python_type, default)

#                     model_name = input_schema.get("title") or f"{tool_name}Args"
#                     pydantic_model = create_model(model_name, **fields)
#                 except Exception as e:
#                     print(f"Error creating Pydantic model for tool {tool_name}: {e}")

#             # 🧠 Fix closure issue by using default args in function factory
#             def make_tool_func(name, conn):
#                 async def tool_func(**kwargs):
#                     return await conn.run_tool(name, kwargs)
#                 return tool_func

#             tool_func = make_tool_func(tool_name, connector)

#             if pydantic_model:
#                 tool = StructuredTool.from_function(
#                     func=tool_func,
#                     name=tool_name,
#                     description=description,
#                     args_schema=pydantic_model,
#                     coroutine=tool_func,
#                 )
#             else:
#                 async def fallback_tool_func(input_str: str, name=tool_name, conn=connector):
#                     try:
#                         params = json.loads(input_str)
#                     except json.JSONDecodeError:
#                         return "Invalid input format. Expected JSON string."
#                     return await conn.run_tool(name, params)

#                 tool = StructuredTool.from_function(
#                     func=fallback_tool_func,
#                     name=tool_name,
#                     description=description,
#                     coroutine=fallback_tool_func,
#                 )

#             built_tools.append(tool)

#     return built_tools


import asyncio
import json
from pydantic import create_model
from langchain.tools import StructuredTool

# Your existing create_tool_func rewritten to return (sync_func, async_func)
def create_tool_func(tool_name: str, connector, pydantic_model=None):
    """
    Returns a pair of functions:
    - sync_func: synchronous wrapper for MCP call (blocking)
    - async_func: native async MCP call function
    """

    async def async_func(**kwargs):
        if pydantic_model:
            try:
                kwargs = pydantic_model(**kwargs).dict()
            except Exception as e:
                return f"Invalid input arguments: {e}"
        result = await connector.run_tool(tool_name, kwargs)
        return result

    def sync_func(**kwargs):
        if not pydantic_model and len(kwargs) == 1 and "input_str" in kwargs:
            try:
                kwargs = json.loads(kwargs["input_str"])
            except json.JSONDecodeError:
                return "Input must be valid JSON string representing tool parameters."
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_func(**kwargs))

    return sync_func, async_func


async def build_tools_from_servers():
    built_tools = []

    for server_name, url in MCP_SERVERS.items():
        connector = MCPConnector(url)
        tools_data = await connector.list_tools()

        for tool_info in tools_data:
            tool_name = tool_info.get("name")
            description = tool_info.get("description")
            input_schema = tool_info.get("argument_schema")  # your schema key

            pydantic_model = None
            if input_schema and input_schema.get("type") == "object":
                try:
                    properties = input_schema.get("properties", {})
                    required_fields = input_schema.get("required", [])
                    fields = {}

                    for prop_name, prop_info in properties.items():
                        json_type = prop_info.get("type", "string")
                        python_type = str
                        if json_type == "integer":
                            python_type = int
                        elif json_type == "number":
                            python_type = float
                        elif json_type == "boolean":
                            python_type = bool

                        default = ... if prop_name in required_fields else None
                        fields[prop_name] = (python_type, default)

                    model_name = input_schema.get("title") or f"{tool_name}Args"
                    pydantic_model = create_model(model_name, **fields)
                except Exception as e:
                    print(f"Error creating Pydantic model for tool {tool_name}: {e}")

            # Create sync + async versions of tool func
            sync_func, async_func = create_tool_func(tool_name, connector, pydantic_model)

            # Build StructuredTool with both sync and async handlers
            tool = StructuredTool.from_function(
                func=sync_func,
                coroutine=async_func,
                name=tool_name,
                description=description,
                args_schema=pydantic_model,
            )
            built_tools.append(tool)

    return built_tools







async def get_agent() -> AgentExecutor:
    tools = await build_tools_from_servers()
    print(tools)

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key="AIzaSyDtgUFKK19oVPUwdZ56r31cTSql1gnhhOs",
        temperature=0
    )

    prompt = build_prompt()
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
