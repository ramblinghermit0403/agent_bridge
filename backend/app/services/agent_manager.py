
import json
import logging
import hashlib
from typing import Dict, Any, Tuple, Optional, List
from app.services.agent.agent_factory import create_final_agent_pipeline
from langchain.agents import AgentExecutor

logger = logging.getLogger(__name__)

# Cache structure: user_id -> (AgentExecutor, config_hash)
# We use a simple dict for now. For production with many users, consider an LRU Cache or TTLCache.
_AGENT_CACHE: Dict[str, Tuple[AgentExecutor, str]] = {}

async def _fetch_tool_permissions(user_id: str, server_ids: List[int]) -> Dict[str, bool]:
    """
    Fetches all tool permissions for the user's servers.
    Returns a dict of {tool_name: is_enabled}.
    """
    from app.database.database import AsyncSessionLocal
    from app.models import ToolPermission
    from sqlalchemy.future import select
    
    permissions = {}
    
    if not server_ids:
        return permissions
    
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(ToolPermission).where(
                ToolPermission.user_id == user_id,
                ToolPermission.server_setting_id.in_(server_ids)
            )
            result = await db.execute(stmt)
            for perm in result.scalars().all():
                # Use server_id + tool_name as key to avoid conflicts
                key = f"{perm.server_setting_id}:{perm.tool_name}"
                permissions[key] = perm.is_enabled
    except Exception as e:
        logger.warning(f"Failed to fetch tool permissions for cache hash: {e}")
    
    return permissions

def _compute_config_hash(
    user_servers: Dict[str, Any], 
    model_provider: str, 
    model_name: str,
    tool_permissions: Dict[str, bool] = None
) -> str:
    """
    Computes a stable hash of the user's configuration, including server settings,
    selected model, AND tool permissions.
    """
    try:
        # Sort keys to ensure deterministic JSON
        # Combine servers + model config + tool permissions
        config_data = {
            "servers": user_servers,
            "provider": model_provider,
            "model": model_name,
            "tool_permissions": tool_permissions or {}
        }
        encoded = json.dumps(config_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()
    except Exception as e:
        logger.warning(f"Failed to compute config hash, disabling cache for this request: {e}")
        return ""

async def get_or_create_agent(
    user_id: str, 
    user_servers: Any, 
    model_provider: str = "gemini", 
    model_name: str = "gemini-2.5-flash"
) -> Tuple[AgentExecutor, bool]:
    """
    Retrieves a cached agent or creates a new one if the configuration has changed.
    Now includes tool permissions in the hash to invalidate cache on tool toggle.
    """
    # Extract server IDs for permission lookup
    server_ids = []
    for server_name, server_info in user_servers.items():
        if isinstance(server_info, dict) and server_info.get("id"):
            server_ids.append(server_info["id"])
    
    # Fetch tool permissions to include in hash
    tool_permissions = await _fetch_tool_permissions(user_id, server_ids)
    
    current_hash = _compute_config_hash(user_servers, model_provider, model_name, tool_permissions)
    
    # Check cache
    if user_id in _AGENT_CACHE:
        cached_agent, cached_hash = _AGENT_CACHE[user_id]
        if cached_hash == current_hash and current_hash != "":
            return cached_agent, True
        else:
            logger.info(f"Agent configuration changed for user {user_id}. Rebuilding...")
    
    # Build new agent
    logger.info(f"Building new agent for user {user_id} with model {model_provider}/{model_name}...")
    agent_executor = await create_final_agent_pipeline(
        user_mcp_servers=user_servers, 
        user_id=user_id,
        model_provider=model_provider,
        model_name=model_name
    )
    
    # Update cache
    if current_hash:
        _AGENT_CACHE[user_id] = (agent_executor, current_hash)
        
    return agent_executor, False

def invalidate_agent_cache(user_id: str):
    """
    Manually invalidate the cache for a user.
    Useful if there are non-config changes that require a rebuild.
    """
    if user_id in _AGENT_CACHE:
        logger.info(f"Invalidating agent cache for user {user_id}")
        del _AGENT_CACHE[user_id]
