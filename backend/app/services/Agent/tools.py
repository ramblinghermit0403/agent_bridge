import asyncio
import json
import logging
from typing import Any, Dict, List
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field, ConfigDict, BaseModel, BaseModel

from ..mcp.connector import MCPConnector

logger = logging.getLogger(__name__)

class ToolException(Exception):
    pass

def create_tool_func(tool_name: str, connector, pydantic_model=None, user_id: str=None, unique_tool_name: str=None, blocking: bool = True):
    """
    Creates the asynchronous and synchronous functions that the LangChain tool will wrap.
    Includes permission checking logic and retry mechanism.
    """
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

    # Define retry strategy: exponential backoff, max 3 attempts
    # We retry on specific exceptions that might be transient
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)), # Add more if needed
        reraise=True
    )
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
        # If blocking is False (used for LangGraph), we SKIP the check here.
        # The Graph is responsible for checking permissions BEFORE calling the tool.
        if blocking and user_id:
            from app.services.security.permissions import save_tool_approval, PendingApproval
            # Create a fresh async session for the check
            from app.database.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                needs_approval, approval_type = await check_tool_approval(db, user_id, tool_name)
                
                if needs_approval and approval_type != 'always':
                    # Logic to block and wait for approval
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


def _sanitize_schema(schema: Any) -> Any:
    """
    Recursively remove unsupported keys from the schema (e.g. title, default)
    to avoid warnings/errors with LangChain & Gemini.
    """
    if isinstance(schema, dict):
        new_schema = schema.copy() # Avoid modifying original in place if possible, though deepcopy is safer
        # Remove offending keys
        for key in ["title", "default", "additionalProperties", "example", "examples"]:
            if key in new_schema:
                del new_schema[key]
        
        # FIX: Gemini requires 'items' for type: array
        if new_schema.get("type") == "array" and "items" not in new_schema:
            new_schema["items"] = {"type": "string"}

        # Recurse for nested dictionaries (e.g. properties)
        for k, v in new_schema.items():
            new_schema[k] = _sanitize_schema(v)
        return new_schema
            
    elif isinstance(schema, list):
        return [_sanitize_schema(item) for item in schema]
    
    return schema

    return built_tools

def _deduplicate_tool_names(tools: List[StructuredTool]) -> List[StructuredTool]:
    """
    Ensures that all tools in the list have unique names.
    If duplicates are found, appends _2, _3, etc.
    """
    seen_names = {}
    
    for tool in tools:
        original_name = tool.name
        if original_name in seen_names:
            count = seen_names[original_name]
            seen_names[original_name] += 1
            new_name = f"{original_name}_{count}"
            tool.name = new_name
            tool.description = f"{tool.description} (Variant {count})"
            # Note: We don't change the function name, just the tool name exposed to LLM
        else:
            seen_names[original_name] = 2 # Next one will be _2
            
    return tools

async def build_tools_from_servers(user_mcp_servers: Dict[str, Dict[str, Any]], user_id: str = None, blocking: bool = True) -> List[StructuredTool]:
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
                oauth_config = None
                setting_id = None
            else:
                url = server_info.get("url")
                creds = server_info.get("credentials")
                oauth_config = server_info.get("oauth_config")
                setting_id = server_info.get("id")
            
            # Create connector (Lazy init)
            connector = MCPConnector(
                url, 
                credentials=creds, 
                server_name=server_name, 
                oauth_config=oauth_config,
                setting_id=setting_id
            )
            
            # --- CACHE LOGIC START ---
            tools_data = []
            manifest_json = server_info.get("tools_manifest") if isinstance(server_info, dict) else None
            
            if manifest_json:
                try:
                    tools_data = json.loads(manifest_json)
                    # logger.info(f"Loaded {len(tools_data)} tools from cache for {server_name}")
                except Exception as e:
                    logger.warning(f"Failed to parse tool cache for {server_name}, falling back to network: {e}")
                    manifest_json = None # Fallback
            
            if not manifest_json:
                # Fallback to network call
                # logger.info(f"Fetching tools via network for {server_name}...")
                try:
                    tools_data = await connector.list_tools()
                except Exception as e:
                    logger.error(f"Skipping tools for server '{server_name}' due to connection error: {e}")
                    continue
            # --- CACHE LOGIC END ---
            
            # Get all permissions for this server/user in ONE batch query (Avoid N+1 bottleneck)
            disabled_tools = set()
            if user_id and setting_id:
                from app.database.database import AsyncSessionLocal
                from app.models import ToolPermission
                from sqlalchemy.future import select
                
                async with AsyncSessionLocal() as db:
                    # Select all permission records for this user and server
                    stmt = select(ToolPermission).where(
                        ToolPermission.user_id == user_id,
                        ToolPermission.server_setting_id == setting_id
                    )
                    result = await db.execute(stmt)
                    perms = result.scalars().all()
                    
                    # Store as a dict for quick lookup
                    perm_map = {p.tool_name: p.is_enabled for p in perms}
                    
                    for tool_info in tools_data:
                        t_name = tool_info.get("name")
                        # Default is enabled if no record exists
                        is_enabled = perm_map.get(t_name, True)
                        if not is_enabled:
                            disabled_tools.add(t_name)
                            logger.info(f"Tool '{t_name}' is DISABLED for user {user_id}, skipping.")

            for tool_info in tools_data:
                tool_name = tool_info.get("name")
                
                # Skip disabled tools
                if tool_name in disabled_tools:
                    continue
                    
                description = tool_info.get("description", "No description provided.")
                input_schema = tool_info.get("argument_schema")
                pydantic_model = None

                # Create the Pydantic model dynamically from the tool's schema
                if input_schema and input_schema.get("type") == "object" and "properties" in input_schema:
                    try:
                        # Sanitize schema to remove unsupported keys
                        input_schema = _sanitize_schema(input_schema)
                        
                        properties = input_schema.get("properties", {})
                        required_fields = input_schema.get("required", [])
                        
                        fields = {}
                        for prop_name, prop_info in properties.items():
                            prop_type_str = prop_info.get("type", "string")
                            
                            if prop_type_str == "array":
                                items_type = prop_info.get("items", {}).get("type", "string")
                                if items_type == "object":
                                    python_type = List[Dict[str, Any]]
                                elif items_type == "integer":
                                    python_type = List[int]
                                elif items_type == "number":
                                    python_type = List[float]
                                elif items_type == "boolean":
                                    python_type = List[bool]
                                else:
                                    python_type = List[str]
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
                        
                        # Create dynamic model
                        class ToolModel(BaseModel):
                            model_config = ConfigDict(title=None)

                        pydantic_model = create_model(
                            model_name, 
                            __base__=ToolModel,
                            **fields
                        )

                    except Exception as e:
                        logger.error(f"Error creating Pydantic model for tool '{tool_name}': {e}", exc_info=True)
                        continue # Skip this tool if its model can't be created
                
                # Use server name in tool name to avoid collisions across servers
                # Sanitized to remove spaces/special chars if needed, but keep uniqueness
                # FIX: Ensure uniqueness below
                sanitized_server_name = server_name.replace(' ', '')
                unique_tool_name = f"{sanitized_server_name}_{tool_name}"
                full_description = f"{description} This tool is from the '{server_name}' server."

                sync_func, async_func = create_tool_func(tool_name, connector, pydantic_model, user_id=user_id, unique_tool_name=unique_tool_name, blocking=blocking)
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
            
    # Final Deduplication Pass
    built_tools = _deduplicate_tool_names(built_tools)
    return built_tools

def create_tool_search_tool(tool_registry: Any, user_id: str):
    """
    Creates a tool that allows the agent to search for other tools.
    """
    class ToolSearchInput(BaseModel):
        query: str = Field(..., description="The search query to find relevant tools.")
    
    async def search_tools_func(query: str):
        tools = tool_registry.search(query, limit=5)
        return [
            {"name": t.name, "description": t.description} 
            for t in tools
        ]

    return StructuredTool.from_function(
        func=lambda query: tool_registry.search(query, limit=5), # sync fallback
        coroutine=search_tools_func,
        name="search_tools",
        description="Search for available tools based on a query. Use this to find tools that can help you verify your task.",
        args_schema=ToolSearchInput
    )
