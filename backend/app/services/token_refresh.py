"""
Token refresh utility for MCP server OAuth tokens.
Handles automatic token refresh when access tokens expire.
"""
import httpx
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# 5-minute buffer before actual expiry
TOKEN_REFRESH_BUFFER_SECONDS = 300


def is_token_expired(credentials: dict) -> bool:
    """
    Check if the access token is expired or about to expire.
    
    Args:
        credentials: Dict containing token info with 'expires_at' timestamp
        
    Returns:
        True if token is expired or will expire within buffer period
    """
    if not credentials or "expires_at" not in credentials:
        # No expiry info - assume valid (will fail naturally if actually expired)
        return False
    
    expires_at = credentials.get("expires_at")
    if not expires_at:
        return False
    
    # Get current time as Unix timestamp
    now = int(datetime.now(timezone.utc).timestamp())
    
    # Check if expired or will expire within buffer
    return now >= (expires_at - TOKEN_REFRESH_BUFFER_SECONDS)


async def refresh_oauth_token(
    server_name: str,
    credentials: dict,
    oauth_config: dict
) -> Optional[Dict]:
    """
    Refresh an expired OAuth token using the refresh_token.
    
    Args:
        server_name: Name of the MCP server (e.g., "GitHub", "Notion")
        credentials: Current credentials dict with refresh_token
        oauth_config: OAuth configuration with token_url and client credentials
        
    Returns:
        Updated credentials dict with new access_token and expires_at,
        or None if refresh fails
    """
    refresh_token = credentials.get("refresh_token")
    if not refresh_token:
        logger.warning(f"No refresh_token available for {server_name}")
        return None
    
    token_url = oauth_config.get("token_url")
    if not token_url:
        logger.error(f"No token_url configured for {server_name}")
        return None
    
    client_id = oauth_config.get("client_id")
    client_secret = oauth_config.get("client_secret")
    
    if not client_id:
        logger.error(f"No client_id configured for {server_name}")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Prepare refresh request
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            
            # Use Basic Auth if client_secret is available
            auth = httpx.BasicAuth(client_id, client_secret) if client_secret else None
            
            logger.info(f"Refreshing token for {server_name}")
            
            response = await client.post(
                token_url,
                data=data,
                auth=auth,
                headers={"Accept": "application/json"},
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed for {server_name}: {response.status_code} - {response.text}")
                return None
            
            token_data = response.json()
            
            # Calculate new expiry timestamp
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            expires_at = int(datetime.now(timezone.utc).timestamp()) + expires_in
            
            # Build updated credentials
            updated_credentials = {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token", refresh_token),  # Use new or keep old
                "expires_at": expires_at,
                "token_type": token_data.get("token_type", "Bearer")
            }
            
            logger.info(f"Successfully refreshed token for {server_name}")
            return updated_credentials
            
    except httpx.TimeoutException:
        logger.error(f"Timeout while refreshing token for {server_name}")
        return None
    except Exception as e:
        logger.error(f"Error refreshing token for {server_name}: {e}")
        return None
