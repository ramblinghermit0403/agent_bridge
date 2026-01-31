# main.py
from typing import List, Optional
import asyncio
from fastapi import HTTPException, Depends,status
from sqlalchemy.exc import IntegrityError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import APIRouter
from ..schemas.settings import McpServerSettingCreate, McpServerSettingRead, McpServerSettingUpdate
from ..models.settings import McpServerSetting 
from ..services.mcp.connector import MCPConnector
from ..auth.oauth2 import get_current_user
from ..models import User
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import database
from sqlalchemy import select

import base64
import hashlib
import secrets


# Configure CORS (adjust origins as per your frontend's URL)

# Pydantic model for the connection test request
class McpConnectionTestRequest(BaseModel):
    server_url: str

router = APIRouter()

# --- Updated API Routes ---

# Route to test MCP server connection (no change needed here as it doesn't depend on a specific user)
@router.post("/api/mcp/test-connection")
async def test_mcp_connection(request: McpConnectionTestRequest):
    """
    Tests the connection to a given MCP server URL by attempting to list tools.
    """
    try:
        # Assuming MCPConnector is a class that handles the connection logic
        connector = MCPConnector(server_url=request.server_url)
        await connector.list_tools()
        return {"status": "success", "message": "Connection to MCP server successful."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to MCP server: {str(e)}"
        )

# Helper function to refresh manifest
async def _refresh_manifest_internal(setting_id: int, db: AsyncSession, current_user: User):
    db_setting = await db.get(McpServerSetting, setting_id)
    if not db_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    
    # 1. Prepare credentials
    import json
    credentials = None
    oauth_config = None
    if db_setting.credentials:
        try:
            creds_data = json.loads(db_setting.credentials)
            credentials = creds_data
            oauth_config = creds_data.get("oauth_config")
        except:
            pass
            
    # 2. Connect and Fetch Tools
    # 2. Connect and Fetch Tools
    # Let exceptions bubble up so they can be handled by the caller or global exception handler
    connector = MCPConnector(
        server_url=db_setting.server_url,
        credentials=credentials,
        server_name=db_setting.server_name,
        setting_id=setting_id,
        oauth_config=oauth_config,
        db_session=db
    )
    tools = await connector.list_tools()
    
    # 3. Update Database
    import datetime
    db_setting.tools_manifest = json.dumps(tools)
    db_setting.last_synced_at = datetime.datetime.utcnow()
    db.add(db_setting)
    await db.commit()
    await db.refresh(db_setting)
    
    return tools

# Route to create a new MCP server setting
@router.post("/api/mcp/settings/", response_model=McpServerSettingRead)
async def create_mcp_setting(
    setting: McpServerSettingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Creates a new MCP server setting for the authenticated user, using the user's ID
    from the authentication token. It immediately attempts to fetch and cache tool definitions.
    """
    # 0. Validate URL
    from urllib.parse import urlparse
    try:
        result = urlparse(setting.server_url)
        if not all([result.scheme, result.netloc]):
             raise ValueError
    except:
        raise HTTPException(status_code=400, detail="Invalid server URL provided.")

    # 1. Check Uniqueness
    stmt = select(McpServerSetting).where(
        McpServerSetting.user_id == current_user.id,
        (McpServerSetting.server_name == setting.server_name) | (McpServerSetting.server_url == setting.server_url)
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="A server with this name or URL already exists."
        )

    # 2. Test Connection (for non-Auth / non-OAuth)
    # If it's a simple SSE server without auth, verify it works before saving.
    # We skip this for OAuth servers or if explicit credentials are provided (though new setting usually implies no creds yet)
    if not setting.requires_oauth:
         try:
             # Assuming MCPConnector is imported
             connector = MCPConnector(server_url=setting.server_url)
             await connector.list_tools()
         except Exception as e:
             raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")

    # Create the database model instance by first converting the Pydantic model to a dict,
    # then adding the user ID from the authenticated user.
    db_setting_data = setting.model_dump()
    # Remove transient field not in DB
    db_setting_data.pop("requires_oauth", None)
    
    db_setting_data["user_id"] = current_user.id
    
    db_setting = McpServerSetting(**db_setting_data)

    try:
        db.add(db_setting)
        await db.commit()
        await db.refresh(db_setting)
        
        # --- NEW: Immediately cache tools ---
        # (This might be redundant if we just tested it, but ensures background cache is populated properly)
        await _refresh_manifest_internal(db_setting.id, db, current_user)
        # ------------------------------------
        
        return db_setting
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A setting with this name already exists for this user."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create setting: {str(e)}"
        )

# Route to get all MCP server settings for the current user
@router.get("/api/mcp/settings/", response_model=List[McpServerSettingRead])
async def read_mcp_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Retrieves all MCP server settings for the authenticated user.
    """
    # Filter by the authenticated user's ID
    statement = select(McpServerSetting).where(McpServerSetting.user_id == current_user.id)
    result = await db.execute(statement)
    settings = result.scalars().all()
    return settings

# Alias endpoint for frontend compatibility
@router.get("/api/settings/mcp-servers", response_model=List[McpServerSettingRead])
async def read_mcp_servers_alias(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Alias for /api/mcp/settings/ - retrieves all MCP server settings for the authenticated user.
    """
    statement = select(McpServerSetting).where(McpServerSetting.user_id == current_user.id)
    result = await db.execute(statement)
    settings = result.scalars().all()
    return settings

# Route to update an MCP server setting
@router.patch("/api/mcp/settings/{setting_id}", response_model=McpServerSettingRead)
async def update_mcp_setting(
    setting_id: int,
    setting_update: McpServerSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Updates an existing MCP server setting by ID, ensuring it belongs to the authenticated user.
    """
    db_setting = await db.get(McpServerSetting, setting_id)
    if not db_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    
    # Crucial security check: Ensure the setting belongs to the current user
    if db_setting.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this setting.")
    
    # Apply updates from the Pydantic model, excluding the user_id
    # to ensure it cannot be changed via the API.
    setting_data = setting_update.model_dump(exclude_unset=True, exclude={"user_id"})
    for key, value in setting_data.items():
        setattr(db_setting, key, value)
    
    try:
        db.add(db_setting)
        await db.commit()
        await db.refresh(db_setting)
        return db_setting
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {str(e)}"
        )

# Route to delete an MCP server setting
@router.delete("/api/mcp/settings/{setting_id}")
async def delete_mcp_setting(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Deletes an MCP server setting by ID, ensuring it belongs to the authenticated user.
    """
    db_setting = await db.get(McpServerSetting, setting_id)
    if not db_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    
    # Crucial security check: Ensure the setting belongs to the current user
    if db_setting.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this setting.")
    
    try:
        await db.delete(db_setting)
        await db.commit()
        return {"message": "Setting deleted successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete setting: {str(e)}"
        )



# Route to get server presets
@router.get("/api/mcp/presets")
async def get_server_presets():
    """
    Returns the list of presets from servers.json.
    """
    import os
    import json
    config_path = "servers.json"
    if not os.path.exists(config_path):
        return {}
        
    try:
        def read_config_sync():
            with open(config_path, 'r') as f:
                return json.load(f)

        data = await asyncio.to_thread(read_config_sync)
        # Return presets if available
        return data.get("presets", {})
    except Exception as e:
        logger.error(f"Failed to load presets: {e}")
        return {}

# Define router.post for refresh BEFORE usage to allow referencing
@router.post("/api/mcp/settings/{setting_id}/refresh")
async def refresh_mcp_setting(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Force-refresh the tools manifest from the remote server.
    """
    db_setting = await db.get(McpServerSetting, setting_id)
    if not db_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    if db_setting.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    await _refresh_manifest_internal(setting_id, db, current_user)
    return {"status": "success", "message": "Tools refreshed successfully"}

# Route to list tools for a specific MCP server setting (DEPRECATED: see tool_permissions.py)
@router.get("/api/mcp/settings/{setting_id}/tools-deprecated")
async def list_server_tools(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Lists tools for a specific MCP server configuration, using stored credentials.
    """
    db_setting = await db.get(McpServerSetting, setting_id)
    if not db_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    
    if db_setting.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        credentials = None
        oauth_config = None
        
        if db_setting.credentials:
            import json
            try:
                creds_data = json.loads(db_setting.credentials)
                credentials = creds_data # Pass full object or sub-keys? MCPConnector expects dict.
                # Extract oauth_config if present
                oauth_config = creds_data.get("oauth_config")
            except json.JSONDecodeError:
                logger.error("Failed to decode credentials JSON")
                pass

        connector = MCPConnector(
            server_url=db_setting.server_url, 
            credentials=credentials,
            server_name=db_setting.server_name,
            setting_id=setting_id,
            oauth_config=oauth_config
        )
        tools = await connector.list_tools()
        return {"status": "success", "tools": tools}
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )

# API Route to reconnect/refresh connection
@router.post("/api/mcp/settings/{setting_id}/reconnect")
async def reconnect_mcp_setting(
    setting_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Reconnects to an MCP server:
    1. Verifies setting ownership.
    2. Instantiates Connector with stored credentials.
    3. Calls list_tools() which handles connection verification and token refresh.
    Returns success status.
    """
    db_setting = await db.get(McpServerSetting, setting_id)
    if not db_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    
    if db_setting.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    # Trigger refresh
    await _refresh_manifest_internal(setting_id, db, current_user)
    
    return {"status": "success", "message": f"Successfully reconnected to {db_setting.server_name}"}

from fastapi import Depends, HTTPException
from pydantic import BaseModel, EmailStr
# ... your existing imports for User, get_current_user, etc.

class UserUpdate(BaseModel):
    username: str
    email: EmailStr

# Assuming UserOut is defined as before
class UserOut(BaseModel):
    username: str
    email: str

@router.put("/users/me", response_model=UserOut)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Update the username and email for the currently authenticated user.
    """
    # Here, you would interact with your database to update the user record
    # This is a conceptual example. Your database logic will vary.
    
    # Example (replace with your actual DB update logic):
    db_user = current_user
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.username = user_update.username
    db_user.email = user_update.email

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user

# --- MCP OAuth Flow ---
import logging
from ..services.mcp.auth import MCPAuthService

logger = logging.getLogger(__name__)

class OAuthInitRequest(BaseModel):
    server_name: str
    server_url: str = None  # Added for custom server support
    client_id: str = None # Optional if server-side configured
    client_secret: str = None # Optional if server-side configured
    redirect_uri: str
    scope: str = None # Added for custom server support
    authorization_url: str = None # Advanced custom config
    token_url: str = None # Advanced custom config
    setting_id: Optional[int] = None # To distinguish Update vs Create

class InspectRequest(BaseModel):
    server_url: str

@router.post("/api/mcp/inspect")
async def inspect_server(request: InspectRequest):
    try:
        report = await MCPAuthService.inspect_server(request.server_url)
        return report
    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/mcp/oauth/init")
async def init_oauth_flow(request: OAuthInitRequest):
    try:
        auth_url = await MCPAuthService.init_oauth_flow(
            server_name=request.server_name,
            server_url=request.server_url,
            redirect_uri=request.redirect_uri,
            client_id=request.client_id,
            client_secret=request.client_secret,
            scope=request.scope,
            authorization_url=request.authorization_url,
            token_url=request.token_url,
            setting_id=request.setting_id
        )
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Failed to init OAuth: {e}")
        raise e # Let global handler or the logic inside service handle HTTP exceptions

@router.get("/api/mcp/oauth/callback")
async def oauth_callback(code: str, state: str):
    """
    Serves a simple HTML page that posts the code/state back to the opener.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auth Success</title>
    </head>
    <body>
        <p>Authentication successful. You can close this window.</p>
        <script>
            // Send the code and state back to the main window
            window.opener.postMessage({{
                type: 'oauth-callback',
                code: '{code}',
                state: '{state}'
            }}, '*');
            
            // Close this popup
            window.close();
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content, status_code=200)

@router.post("/api/mcp/oauth/finalize")
async def finalize_oauth_flow(
    code: str, 
    state: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    try:
        data = await MCPAuthService.finalize_oauth_flow(code, state)
        
        server_name = data['server_name']
        server_url = data['server_url']
        credentials_json = data['credentials']
        setting_id = data.get('setting_id')

        existing_setting = None

        if setting_id:
            # STRICT UPDATE: We only update the specific setting we initiated auth for
            stmt = select(McpServerSetting).where(
                McpServerSetting.id == setting_id, 
                McpServerSetting.user_id == current_user.id
            )
            existing_setting = (await db.execute(stmt)).scalars().first()
            if not existing_setting:
                logger.warning(f"Finalize: Setting {setting_id} not found/owned.")
                raise HTTPException(status_code=404, detail="Connection setting not available for update.")
        else:
            # UPSERT LOGIC: If a server with this Name or URL already exists, update it instead of failing
            stmt = select(McpServerSetting).where(
                McpServerSetting.user_id == current_user.id,
                (McpServerSetting.server_name == server_name) | (McpServerSetting.server_url == server_url)
            )
            existing_setting = (await db.execute(stmt)).scalars().first()
            if existing_setting:
                logger.info(f"Finalize: Found existing server '{existing_setting.server_name}' for upsert.")

        # Extract explicitly requested fields from credentials
        import json
        creds_dict = json.loads(credentials_json)
        expires_at_val = creds_dict.get('expires_at')
        
        oauth_config = creds_dict.get('oauth_config', {})
        
        client_id_val = oauth_config.get('client_id')
        client_secret_val = oauth_config.get('client_secret')
        authorization_url_val = oauth_config.get('authorization_url') 
        token_url_val = oauth_config.get('token_url')

        if existing_setting:
            existing_setting.server_url = server_url
            existing_setting.is_active = True
            existing_setting.credentials = credentials_json
            existing_setting.client_id = client_id_val
            existing_setting.client_secret = client_secret_val
            existing_setting.authorization_url = authorization_url_val
            existing_setting.token_url = token_url_val
            existing_setting.expires_at = expires_at_val
            db.add(existing_setting)
        else:
            new_setting = McpServerSetting(
                user_id=current_user.id,
                server_name=server_name,
                server_url=server_url,
                is_active=True,
                description="Connected via Managed OAuth",
                credentials=credentials_json,
                client_id=client_id_val,
                client_secret=client_secret_val,
                authorization_url=authorization_url_val,
                token_url=token_url_val,
                expires_at=expires_at_val
            )
            db.add(new_setting)
            
        await db.commit()
        return {"status": "success", "server_url": server_url}
        
    except Exception as e:
        logger.error(f"Finalize failed: {e}")
        raise e