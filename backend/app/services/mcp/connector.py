import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
import httpx
import json
import logging
import logging
from sqlalchemy import select
from ...database.database import AsyncSessionLocal

import logging
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

# Module-level cache for tool lists: (server_url, token_hash) -> (tools_data, timestamp)
_TOOLS_CACHE: Dict[str, Any] = {}

class MCPConnector:
    """
    Manages persistent connections and tool execution for Model Context Protocol (MCP) servers.

    This class handles:
    - Establishing and maintaining sessions (SSE or HTTP).
    - Authentication and Token Management (OAuth, Refresh).
    - Tool discovery and caching.
    - Reliable tool execution with retries and error handling.

    Attributes:
        server_url (str): The endpoint URL of the MCP server.
        server_name (str): Human-readable name of the server.
        oauth_config (dict): Oauth2 configuration for token refreshes.
        setting_id (int): Database ID of the server setting for persisting credentials.
    """
    def __init__(
        self, 
        server_url: str, 
        credentials: Optional[str] = None,
        server_name: Optional[str] = None,
        oauth_config: Optional[Dict] = None,
        db_session: Optional[Any] = None,
        setting_id: Optional[int] = None
    ):
        """
        Initialize the MCP Connector.

        Args:
            server_url (str): The MCP server URL.
            credentials (str, optional): JSON string or dict of credentials (access_token, refresh_token).
            server_name (str, optional): Name of the server (used for logging and refreshes).
            oauth_config (dict, optional): Config for OAuth flow (client_id, etc.).
            db_session (Any, optional): Storage session (not primarily used here, usually passed to managers).
            setting_id (int, optional): ID to update credentials in the DB.
        """
        self.server_url = server_url
        self.server_name = server_name
        self.oauth_config = oauth_config
        self.db_session = db_session
        self.setting_id = setting_id
        self._parsed_url = urlparse(server_url)
        self._credentials = self._parse_credentials(credentials)
        self._token = self._extract_token()
        
        # Session management
        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._lock = asyncio.Lock()
        
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
    
    async def _ensure_valid_token(self, force_refresh: bool = False) -> bool:
        """
        Check if token is valid and refresh if needed.
        Returns True if token is valid/refreshed, False if refresh failed.
        """
        # Skip if no credentials or no refresh capability
        if not self._credentials or not self.server_name or not self.oauth_config:
            return True  # Assume valid, will fail naturally if not
        
        from .token_manager import is_token_expired, refresh_oauth_token
        
        # Check if token needs refresh
        if not force_refresh and not is_token_expired(self._credentials):
            return True  # Token still valid
        
        logger.info(f"Token expired (or forced) for {self.server_name}, attempting refresh...")
        
        # Attempt refresh
        new_credentials = await refresh_oauth_token(
            self.server_name,
            self._credentials,
            self.oauth_config
        )
        
        if not new_credentials:
            logger.warning(f"Failed to refresh token for {self.server_name}. Checking database for updated credentials...")
            
            # Fallback: Check if credentials have been updated in the DB (e.g. user re-authenticated)
            if self.setting_id:
                try:
                    async with AsyncSessionLocal() as session:
                        from ...models.settings import McpServerSetting
                        stmt = select(McpServerSetting).where(McpServerSetting.id == self.setting_id)
                        result = await session.execute(stmt)
                        setting = result.scalars().first()
                        
                        if setting and setting.credentials:
                            db_creds = json.loads(setting.credentials) if isinstance(setting.credentials, str) else setting.credentials
                            
                            # Check if these DB credentials are strictly "newer" or "valid" compared to what we had
                            # For simplicity, if we have DB creds and our current refresh failed, we try the DB creds.
                            if db_creds:
                                logger.info(f"Found credentials in DB for {self.server_name}, attempting to use them as fallback.")
                                self._credentials = db_creds
                                self._token = db_creds.get("access_token")
                                
                                # Re-check validity of these new credentials
                                # Recurse once with force_refresh=False to check if these new creds are valid
                                # We pass force_refresh=False to avoiding looping if they are also expired but refreshable
                                if not is_token_expired(self._credentials):
                                    new_credentials = self._credentials # Treat as success
                                    logger.info(f"Fallback to DB credentials successful for {self.server_name}")
                                    
                                    # Update headers immediately since we have a valid token now
                                    if "figma.com" in self.server_url:
                                        self._headers = {"X-Figma-Token": self._token}
                                    elif "notion.com" in self.server_url:
                                        self._headers = {
                                            "Authorization": f"Bearer {self._token}",
                                            "Notion-Version": "2022-06-28"
                                        }
                                    else:
                                        self._headers = {"Authorization": f"Bearer {self._token}"}
                                        
                                    return True
                                else:
                                    logger.warning(f"DB credentials for {self.server_name} are also expired.")
                                    # If DB creds are also expired, we could try to refresh THEM, 
                                    # but let's avoid infinite recursion. One level of fallback is usually enough.
                except Exception as db_e:
                    logger.error(f"Error fetching fallback credentials from DB: {db_e}")

            # If still no new_credentials after fallback attempt
            if not new_credentials:
                from .exceptions import RequiresAuthenticationError
                logger.error(f"Token refresh and DB fallback failed for {self.server_name}, flagging for re-auth")
                raise RequiresAuthenticationError(self.server_name)
        
        # Update credentials
        # IMPORTANT: Preserve original oauth_config as token_manager doesn't return it
        if self._credentials and "oauth_config" in self._credentials:
            new_credentials["oauth_config"] = self._credentials["oauth_config"]
            
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
        
        # Update database if we have a setting_id
        if self.setting_id:
            try:
                # Use a fresh session for the update to ensure it persists correctly
                # regardless of the original request's session state.
                async with AsyncSessionLocal() as session:
                    from ...models.settings import McpServerSetting
                    stmt = select(McpServerSetting).where(McpServerSetting.id == self.setting_id)
                    result = await session.execute(stmt)
                    setting = result.scalars().first()
                    
                    if setting:
                        setting.credentials = json.dumps(new_credentials)
                        # Also update top-level columns for consistency
                        if "expires_at" in new_credentials:
                            setting.expires_at = new_credentials["expires_at"]
                        
                        session.add(setting)
                        await session.commit()
                        logger.info(f"Updated credentials and expires_at in database for {self.server_name} (Setting ID: {self.setting_id})")
                    else:
                        logger.warning(f"Setting ID {self.setting_id} not found in database while trying to update token.")
            except Exception as e:
                logger.error(f"Failed to update credentials in database: {e}")
        
        return True

    async def list_tools(self) -> List[Dict[str, Any]]:
        # 0. Ensure token is valid BEFORE checking cache
        # This prevents returning cached tools when the user's session is actually expired
        if not await self._ensure_valid_token():
             # Should practically unreachable as _ensure_valid_token raises exceptions on failure
             raise RuntimeError(f"Token validation failed for {self.server_name}")

        # 1. Check module-level cache
        cache_key = f"{self.server_url}:{hash(str(self._token))}"
        if cache_key in _TOOLS_CACHE:
            logger.info(f"Returning cached tools for {self.server_name or self.server_url}")
            return _TOOLS_CACHE[cache_key]

        # 2. Execute and cache
        tools = await self._execute_with_retry(self._list_tools_internal)
        _TOOLS_CACHE[cache_key] = tools
        return tools

    async def _get_session(self) -> ClientSession:
        """
        Returns a persistent session, creating it if necessary.
        """
        async with self._lock:
            if self._session:
                return self._session

            logger.info(f"Initializing persistent MCP session for {self.server_name or self.server_url}")
            self._exit_stack = AsyncExitStack()
            
            try:
                # Determine method
                try:
                    # SSE
                    ctx = sse_client(self.server_url, headers=self._headers)
                    read_stream, write_stream = await self._exit_stack.enter_async_context(ctx)
                except Exception as e:
                    logger.warning(f"SSE failed for {self.server_url}, trying Streamable HTTP: {e}")
                    ctx = streamablehttp_client(self.server_url, headers=self._headers)
                    read_stream, write_stream, _ = await self._exit_stack.enter_async_context(ctx)

                self._session = await self._exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                await self._session.initialize()
                return self._session
            except Exception as e:
                if self._exit_stack:
                    await self._exit_stack.aclose()
                self._exit_stack = None
                self._session = None
                raise e

    async def close(self):
        """Clean up the persistent session."""
        async with self._lock:
            if self._exit_stack:
                await self._exit_stack.aclose()
            self._exit_stack = None
            self._session = None

    async def _list_tools_internal(self):
        session = await self._get_session()
        tools_result = await session.list_tools()
        return await self._process_tools_result(tools_result)

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """
        Generic retry logic for authentication and transient network errors.

        Strategy:
        1. Validate token.
        2. Attempt operation.
        3. On Auth Error (401): Force refresh token and retry.
        4. On Transient Error (Timeout/Connection): Clear session and retry once.

        Args:
            operation (Callable): Async function to execute.
            *args: Positional args for operation.
            **kwargs: Keyword args for operation.

        Returns:
            Any: The result of the operation.

        Raises:
            RequiresAuthenticationError: If re-auth is needed even after refresh.
            RuntimeError: If token validation fails hard.
            Exception: Original exception if not handled by retry logic.
        """
        # Helper to detect transient/connection errors
        def is_transient_exception(exc):
            """Check if exception is a transient network/connection error."""
            transient_types = (
                ConnectionError,
                ConnectionResetError,
                ConnectionRefusedError,
                ConnectionAbortedError,
                TimeoutError,
                asyncio.TimeoutError,
                OSError,  # Covers many network-level errors
            )
            # Direct type check
            if isinstance(exc, transient_types):
                return True
            # Check error message for common transient patterns
            msg = str(exc).lower()
            transient_patterns = [
                "connection reset", "connection refused", "connection closed",
                "timed out", "timeout", "temporarily unavailable",
                "network unreachable", "broken pipe", "eof",
            ]
            if any(p in msg for p in transient_patterns):
                return True
            # Check nested exceptions
            if getattr(exc, '__cause__', None) and is_transient_exception(exc.__cause__):
                return True
            if getattr(exc, '__context__', None) and is_transient_exception(exc.__context__):
                return True
            if hasattr(exc, 'exceptions'):
                for sub_exc in exc.exceptions:
                    if is_transient_exception(sub_exc):
                        return True
            return False

        # Recursively check for 401 or auth-related errors in exceptions and nested groups
        def is_auth_exception(exc):
            msg = str(exc).lower()
            if "401" in msg or "unauthorized" in msg or "authentication failed" in msg:
                return True
            # Check direct cause or context
            if getattr(exc, '__cause__', None) and is_auth_exception(exc.__cause__):
                return True
            if getattr(exc, '__context__', None) and is_auth_exception(exc.__context__):
                return True
            # Check nested exceptions (ExceptionGroup / TaskGroup)
            if hasattr(exc, 'exceptions'):
                for sub_exc in exc.exceptions:
                    if is_auth_exception(sub_exc):
                        return True
            return False

        # 1. Initial Standard Check
        if not await self._ensure_valid_token():
             raise RuntimeError(f"Token refresh failed for {self.server_name}. Please re-authenticate.")

        try:
            return await operation(*args, **kwargs)
        except Exception as e:
            # Priority 1: Auth errors -> Refresh token and retry
            if is_auth_exception(e):
                logger.warning(f"Authentication failed for {self.server_name} (Error: {e}). Forcing token refresh and retrying...")
                
                # Force Refresh
                if await self._ensure_valid_token(force_refresh=True):
                    # Clear stale session before retry
                    await self.close()
                    try:
                        logger.info(f"Retrying operation for {self.server_name} with new token...")
                        return await operation(*args, **kwargs)
                    except Exception as retry_e:
                        logger.error(f"Retry failed for {self.server_name}: {retry_e}")
                        if is_auth_exception(retry_e):
                             from .exceptions import RequiresAuthenticationError
                             raise RequiresAuthenticationError(self.server_name)
                        raise retry_e
                else:
                     raise RuntimeError(f"Forced token refresh failed for {self.server_name}. Please re-authenticate.")
            
            # Priority 2: Transient errors -> Clear session and retry once
            elif is_transient_exception(e):
                logger.warning(f"Transient error for {self.server_name} (Error: {e}). Clearing session and retrying...")
                await self.close()  # Clear dead session
                try:
                    logger.info(f"Retrying operation for {self.server_name} with fresh connection...")
                    return await operation(*args, **kwargs)
                except Exception as retry_e:
                    logger.error(f"Retry after transient error failed for {self.server_name}: {retry_e}")
                    raise retry_e
            
            else:
                raise e

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

    async def run_tool(self, tool_name: str, parameters: dict):
        """
        Executes a specific tool on the MCP server.

        Wraps the execution in `_execute_with_retry` to handle potential
        session timeouts or expired tokens automatically.

        Args:
            tool_name (str): The name of the tool to run.
            parameters (dict): The arguments to pass to the tool.

        Returns:
            str or Any: The tool output or error message.
        """
        async def _run_tool_internal(tool_name, parameters):
            session = await self._get_session()
            try:
                result = await asyncio.wait_for(session.call_tool(tool_name, parameters), timeout=60.0)
                return result.output if hasattr(result, "output") else result
            except Exception as e:
                # If call failed, maybe session is dead, clear it so next call retries
                logger.warning(f"Tool call failed for {tool_name}, clearing session: {e}")
                await self.close()
                raise e

        try:
             return await self._execute_with_retry(_run_tool_internal, tool_name, parameters)
        except Exception as e:
             # Final fallback to return string error so agent doesn't crash
             return f"Error: Tool execution failed for {self.server_name}. {str(e)}"

