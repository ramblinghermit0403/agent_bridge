import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
import httpx
import json
import logging

logger = logging.getLogger(__name__)

class MCPConnector:
    def __init__(self, server_url: str, credentials: Optional[str] = None):
        self.server_url = server_url
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

    async def list_tools(self) -> List[Dict[str, Any]]:
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
        logger.info(f"Connecting via SSE to {self.server_url} with headers: {self._headers.keys()}")
        # headers supported in newer mcp versions for sse_client
        async with sse_client(self.server_url, headers=self._headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return await self._process_tools_result(tools_result)

    async def _list_tools_streamable(self):
        logger.info(f"Connecting via Streamable HTTP to {self.server_url} with headers: {self._headers.keys()}")
        # Create httpx client with headers (new API requirement)
        async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
            async with streamable_http_client(self.server_url, http_client=client) as (read, write, get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    return await self._process_tools_result(tools_result)

    async def run_tool(self, tool_name: str, parameters: dict):
        try:
            return await self._run_tool_sse(tool_name, parameters)
        except Exception as e:
            logger.warning(f"SSE run_tool failed for {tool_name}: {e}. Trying Streamable HTTP...")
            # Fallback
            return await self._run_tool_streamable(tool_name, parameters)

    async def _run_tool_sse(self, tool_name: str, parameters: dict):
         async with sse_client(self.server_url, headers=self._headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=10.0)
                # 60s timeout for tool execution
                result = await asyncio.wait_for(session.call_tool(tool_name, parameters), timeout=60.0)
                return result.output if hasattr(result, "output") else result

    async def _run_tool_streamable(self, tool_name: str, parameters: dict):
        # Create httpx client with headers (new API requirement)
        async with httpx.AsyncClient(headers=self._headers, timeout=httpx.Timeout(30.0, read=60.0)) as client:
            async with streamable_http_client(self.server_url, http_client=client) as (read, write, get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, parameters)
                    return result.output if hasattr(result, "output") else result
