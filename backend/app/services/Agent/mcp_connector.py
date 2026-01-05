import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
import httpx
import json
import logging
from sqlalchemy import select

logger = logging.getLogger(__name__)

class MCPConnector:
    def __init__(
        self, 
        server_url: str, 
        credentials: Optional[str] = None,
        server_name: Optional[str] = None,
        oauth_config: Optional[Dict] = None,
        db_session: Optional[Any] = None,
        setting_id: Optional[int] = None
    ):
        self.server_url = server_url
        self.server_name = server_name
        self.oauth_config = oauth_config
        self.db_session = db_session
        self.setting_id = setting_id
        self._parsed_url = urlparse(server_url)
        self._credentials = self._parse_credentials(credentials)
        self._token = self._extract_token()
        
        # Determine header format based on server
        if "figma.com" in server_url:
            header_name = "X-Figma-Token"
            header_val = self._token
        elif "notion.com" in server_url:
            header_name = "Authorization"
            header_val = f"Bearer {self._token}"
            # Notion also requires Notion-Version header
            self._headers = {
                header_name: header_val,
                "Notion-Version": "2022-06-28"
            } if self._token else {}
            return
        else:
            header_name = "Authorization"
            header_val = f"Bearer {self._token}"
        
        self._headers = {header_name: header_val} if self._token else {}

    def _parse_credentials(self, creds: Optional[str]) -> Optional[Dict]:
        if not creds: return None
        try:
             return json.loads(creds) if isinstance(creds, str) else creds
        except:
             return None

    def _extract_token(self) -> Optional[str]:
        # 1. Try Credentials (DB)
        if self._credentials and "access_token" in self._credentials:
            return self._credentials["access_token"]
        
        # 2. Try URL Query (Legacy/Fallback)
        query = parse_qs(self._parsed_url.query)
        return query.get("token", [None])[0]
    
    async def _ensure_valid_token(self) -> bool:
        """
        Check if token is valid and refresh if needed.
        Returns True if token is valid/refreshed, False if refresh failed.
        """
        # Skip if no credentials or no refresh capability
        if not self._credentials or not self.server_name or not self.oauth_config:
            return True  # Assume valid, will fail naturally if not
        
        from ..token_refresh import is_token_expired, refresh_oauth_token
        
        # Check if token needs refresh
        if not is_token_expired(self._credentials):
            return True  # Token still valid
        
        logger.info(f"Token expired for {self.server_name}, attempting refresh...")
        
        # Attempt refresh
        new_credentials = await refresh_oauth_token(
            self.server_name,
            self._credentials,
            self.oauth_config
        )
        
        if not new_credentials:
            logger.error(f"Failed to refresh token for {self.server_name}")
            return False
        
        # Update credentials
        self._credentials = new_credentials
        self._token = new_credentials.get("access_token")
        
        # Update headers with new token
        if "figma.com" in self.server_url:
            self._headers = {"X-Figma-Token": self._token}
        elif "notion.com" in self.server_url:
            self._headers = {
                "Authorization": f"Bearer {self._token}",
                "Notion-Version": "2022-06-28"
            }
        else:
            self._headers = {"Authorization": f"Bearer {self._token}"}
        
        # Update database if we have a session and setting_id
        if self.db_session and self.setting_id:
            try:
                from ...models.settings import McpServerSetting
                stmt = select(McpServerSetting).where(McpServerSetting.id == self.setting_id)
                result = await self.db_session.execute(stmt)
                setting = result.scalars().first()
                
                if setting:
                    setting.credentials = json.dumps(new_credentials)
                    self.db_session.add(setting)
                    await self.db_session.commit()
                    logger.info(f"Updated credentials in database for {self.server_name}")
            except Exception as e:
                logger.error(f"Failed to update credentials in database: {e}")
        
        return True

    async def list_tools(self) -> List[Dict[str, Any]]:
        # Ensure token is valid before making API call
        if not await self._ensure_valid_token():
            raise RuntimeError(f"Token refresh failed for {self.server_name}. Please re-authenticate.")
        
        # Try SSE first, then Streamable HTTP
        try:
            return await self._list_tools_sse()
        except Exception as e:
            logger.warning(f"SSE connection failed for {self.server_url}: {e}. Trying Streamable HTTP...")
            try:
                return await self._list_tools_streamable()
            except Exception as e2:
                logger.error(f"Streamable HTTP connection also failed: {e2}")
                raise RuntimeError(f"Could not connect to MCP server via SSE or Streamable HTTP. Last error: {e2}")

    async def _process_tools_result(self, tools_result) -> List[Dict[str, Any]]:
        tool_list = []
        for tool in tools_result.tools:
            input_schema = None
            if hasattr(tool, "inputSchema"):
                if isinstance(tool.inputSchema, str):
                    try:
                        input_schema = json.loads(tool.inputSchema)
                    except json.JSONDecodeError:
                        input_schema = None
                else:
                    input_schema = tool.inputSchema

            tool_list.append({
                "name": tool.name,
                "description": tool.description,
                "argument_schema": input_schema,
            })
        return tool_list

    async def _list_tools_sse(self):
        logger.info(f"Connecting via SSE to {self.server_url}")
        try:
            # Try with headers first (newer MCP)
            async with sse_client(self.server_url, headers=self._headers) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    return await self._process_tools_result(tools_result)
        except TypeError:
            # Fallback for older MCP versions that don't support headers
            logger.warning(f"sse_client rejected headers for {self.server_url}, trying without.")
            async with sse_client(self.server_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    return await self._process_tools_result(tools_result)

    async def _list_tools_streamable(self):
        logger.info(f"Connecting via Streamable HTTP to {self.server_url}")
        async with streamablehttp_client(self.server_url, headers=self._headers) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return await self._process_tools_result(tools_result)

    async def run_tool(self, tool_name: str, parameters: dict):
        # Ensure token is valid before making API call
        if not await self._ensure_valid_token():
            return f"Error: Token refresh failed for {self.server_name}. Please re-authenticate in settings."
        
        try:
            return await self._run_tool_sse(tool_name, parameters)
        except (httpx.ConnectError, Exception) as e:
            logger.warning(f"SSE run_tool failed for {tool_name}: {e}. Trying Streamable HTTP...")
            try:
                # Fallback to Streamable
                return await self._run_tool_streamable(tool_name, parameters)
            except (httpx.ConnectError, Exception) as e2:
                logger.error(f"Tool execution failed for {tool_name} on {self.server_url}: {e2}")
                # Return string error instead of raising to prevent agent crash
                return f"Error: Could not connect to any MCP server at {self.server_url}. Please ensure the server is running. Details: {e2}"

    async def _run_tool_sse(self, tool_name: str, parameters: dict):
         try:
             async with sse_client(self.server_url, headers=self._headers) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    result = await asyncio.wait_for(session.call_tool(tool_name, parameters), timeout=60.0)
                    return result.output if hasattr(result, "output") else result
         except TypeError:
             logger.warning(f"sse_client run_tool rejected headers for {self.server_url}, trying without.")
             async with sse_client(self.server_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    result = await asyncio.wait_for(session.call_tool(tool_name, parameters), timeout=60.0)
                    return result.output if hasattr(result, "output") else result

    async def _run_tool_streamable(self, tool_name: str, parameters: dict):
        # Pass headers to support authentication
        async with streamablehttp_client(self.server_url, headers=self._headers) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, parameters)
                return result.output if hasattr(result, "output") else result
