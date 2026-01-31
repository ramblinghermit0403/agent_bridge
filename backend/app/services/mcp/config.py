from app.models.settings import McpServerSetting
from typing import Dict, Any
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging



logger = logging.getLogger(__name__)

async def get_user_servers(db: AsyncSession, user_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Fetches all ACTIVE McpServerSetting records for a user from the database
    and transforms them into a dictionary suitable for the agent factory.
    
    Format: {"server_name": {"url": "...", "credentials": "...", "oauth_config": {...}}, ...}
    """
    logger.info(f"Fetching active MCP server settings for user_id: {user_id}")

    # 1. Create a statement to select all settings for the given user_id
    statement = (
        select(McpServerSetting)
        .where(McpServerSetting.user_id == user_id)
        .where(McpServerSetting.is_active == True)
    )
    
    # 2. Execute the query
    result = await db.execute(statement)
    user_settings = result.scalars().all()
    
    # 3. Build lookup from stored credentials
    import json
    
    # 4. Transform the list of model objects into a dictionary
    server_dict = {}
    for setting in user_settings:
        # Extract oauth_config from credentials if available
        oauth_config = {}
        if setting.credentials:
            try:
                creds = json.loads(setting.credentials)
                oauth_config = creds.get("oauth_config", {})
            except Exception:
                logger.warning(f"Failed to parse credentials for server {setting.server_name}")

        # Merge with top-level columns if they exist (allows easier manual overrides/fixes)
        if setting.client_id: oauth_config["client_id"] = setting.client_id
        if setting.client_secret: oauth_config["client_secret"] = setting.client_secret
        if setting.authorization_url: oauth_config["authorization_url"] = setting.authorization_url
        if setting.token_url: oauth_config["token_url"] = setting.token_url

        server_dict[setting.server_name] = {
            "id": setting.id,
            "url": setting.server_url,
            "credentials": setting.credentials,
            "oauth_config": oauth_config,
            "tools_manifest": setting.tools_manifest  # NEW: Include cached tool definitions
        }
    
    if server_dict:
        logger.info(f"Found {len(server_dict)} active servers for user {user_id}: {list(server_dict.keys())}")
    else:
        logger.info(f"No active MCP servers found for user {user_id}.")

    return server_dict
