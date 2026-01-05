# main.py
from typing import List
from fastapi import HTTPException, Depends,status
from sqlalchemy.exc import IntegrityError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import APIRouter
from ..schemas.settings import McpServerSettingCreate, McpServerSettingRead, McpServerSettingUpdate
from ..models.settings import McpServerSetting 
from ..services.Agent.mcp_connector import MCPConnector
from ..auth.oauth2 import get_current_user
from ..models import User
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import database
from sqlalchemy import select
from ..core.preapproved_servers import preapproved_mcp_servers
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
        connector = MCPConnector(sse_url=request.server_url)
        await connector.list_tools()
        return {"status": "success", "message": "Connection to MCP server successful."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to MCP server: {str(e)}"
        )

# Route to create a new MCP server setting
@router.post("/api/mcp/settings/", response_model=McpServerSettingRead)
async def create_mcp_setting(
    setting: McpServerSettingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Creates a new MCP server setting for the authenticated user, using the user's ID
    from the authentication token.
    """
    # Create the database model instance by first converting the Pydantic model to a dict,
    # then adding the user ID from the authenticated user.
    db_setting_data = setting.model_dump()
    db_setting_data["user_id"] = current_user.id
    
    db_setting = McpServerSetting(**db_setting_data)

    try:
        db.add(db_setting)
        await db.commit()
        await db.refresh(db_setting)
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

# Route to get preapproved MCP servers
@router.get("/api/mcp/preapproved-servers")
async def get_preapproved_servers():
    """
    Returns a list of preapproved MCP servers.
    Excludes client_secret for security.
    """
    safe_servers = []
    for server in preapproved_mcp_servers:
        server_copy = server.copy()
        if "oauth_config" in server_copy:
            oauth = server_copy["oauth_config"].copy()
            if "client_secret" in oauth:
                del oauth["client_secret"]
            server_copy["oauth_config"] = oauth
        safe_servers.append(server_copy)
    return safe_servers

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
        if db_setting.credentials:
            import json
            try:
                credentials = json.loads(db_setting.credentials)
            except json.JSONDecodeError:
                logger.error("Failed to decode credentials JSON")
                pass

        # Lookup OAuth config from preapproved list
        oauth_config = None
        server_name = db_setting.server_name
        server_info = next((s for s in preapproved_mcp_servers if s['server_name'] == server_name), None)
        if server_info:
            oauth_config = server_info.get('oauth_config')

        connector = MCPConnector(
            server_url=db_setting.server_url, 
            credentials=credentials,
            server_name=server_name,
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
import uuid
import httpx
import logging
from urllib.parse import urlencode, unquote

logger = logging.getLogger(__name__)

# Simple in-memory cache for OAuth states: state -> {client_id, client_secret, redirect_uri, provider}
# In production, use Redis or DB.
oauth_states = {}

class OAuthInitRequest(BaseModel):
    server_name: str
    client_id: str = None # Optional if server-side configured
    client_secret: str = None # Optional if server-side configured
    redirect_uri: str


async def discover_oauth_config(server_url: str):
    """
    Implements MCP 'Smart Auth' discovery:
    1. POST to server_url -> 401 + WWW-Authenticate header.
    2. Extract resource_metadata URL.
    3. Fetch metadata -> get OAuth endpoints.
    """
    logger.info(f"Discovering OAuth config for {server_url}")
    
    # 1. Trigger 401
    async with httpx.AsyncClient() as client:
        try:
            # Send dummy JSON-RPC to trigger auth challenge
            dummy_payload = {
                "jsonrpc": "2.0", 
                "method": "initialize", 
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "discovery", "version": "1.0"}}, 
                "id": 1
            }
            resp = await client.post(server_url, json=dummy_payload)
            
            if resp.status_code != 401:
                logger.warning(f"Expected 401 for discovery, got {resp.status_code}")
                # Fallback: maybe it's not protected or assumes static config?
                return None
            
            auth_header = resp.headers.get("www-authenticate", "")
            if not auth_header:
                return None
                
            # Parse header: Bearer resource_metadata="https://..."
            metadata_url = None
            parts = auth_header.split(",")
            for part in parts:
                if "resource_metadata" in part:
                    # Extract URL found between quotes
                    try:
                        metadata_url = part.split('resource_metadata="')[1].split('"')[0]
                    except IndexError:
                        pass
            
            if not metadata_url:
                logger.warning("No resource_metadata found in WWW-Authenticate header")
                return None
                
            logger.info(f"Fetching metadata from {metadata_url}")
            meta_resp = await client.get(metadata_url)
            if meta_resp.status_code != 200:
                logger.error(f"Failed to fetch metadata: {meta_resp.status_code}")
                return None
                
            metadata = meta_resp.json()
            return {
                "authorization_url": metadata.get("authorization_endpoint"),
                "token_url": metadata.get("token_endpoint")
            }
            
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            return None

@router.post("/api/mcp/oauth/init")
async def init_oauth_flow(request: OAuthInitRequest):
    # Find the server config
    server = next((s for s in preapproved_mcp_servers if s['server_name'] == request.server_name), None)
    if not server:
         raise HTTPException(status_code=400, detail="Server not found")
    
    # 1. Try Dynamic Discovery
    discovered_config = await discover_oauth_config(server['server_url'])
    
    # 2. Fallback to static config
    static_config = server.get('oauth_config', {})
    
    d_config = discovered_config or {}
    print(f"DEBUG: Dynamic: {d_config}")
    print(f"DEBUG: Static: {static_config}")

    auth_url_base = d_config.get('authorization_url') or static_config.get('authorization_url')
    token_url = d_config.get('token_url') or static_config.get('token_url')
    scope = static_config.get('scope', '')
    
    if not auth_url_base or not token_url:
        logger.error(f"Missing Config. Auth: {auth_url_base}, Token: {token_url}")
        raise HTTPException(status_code=400, detail="Could not determine OAuth configuration.")
        
    # Get Credentials: Prefer User Input -> Fallback to Config/Env
    client_id = request.client_id if request.client_id else static_config.get('client_id')
    client_secret = request.client_secret if request.client_secret else static_config.get('client_secret')

    if not client_id:
        raise HTTPException(status_code=400, detail="Client ID missing (not provided or configured).")
    
    # Generate PKCE parameters (required for OAuth 2.1)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    state = str(uuid.uuid4())
    oauth_states[state] = {
        "client_id": client_id,
        "client_secret": client_secret, 
        "redirect_uri": request.redirect_uri,
        "token_url": token_url,
        "server_url": server['server_url'],
        "server_name": server['server_name'],
        "code_verifier": code_verifier  # Store for token exchange
    }
    
    params = {
        "client_id": client_id,
        "redirect_uri": request.redirect_uri,
        "scope": scope,
        "state": state,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    # Notion requires owner=user parameter
    if server['server_name'] == "Notion":
        params["owner"] = "user"
    
    auth_url = f"{auth_url_base}?{urlencode(params)}"
    return {"auth_url": auth_url}

@router.get("/api/mcp/oauth/callback")
async def oauth_callback(code: str, state: str):
    """
    Serves a simple HTML page that posts the code/state back to the opener
    (the frontend app) and then closes the popup.
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
    print(f"DEBUG: Finalize called with code={code}, state={state}")
    stored_state = oauth_states.pop(state, None)
    if not stored_state:
        print("DEBUG: State not found in oauth_states")
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    print(f"DEBUG: Found state. Token URL: {stored_state['token_url']}")

    credentials_json = None
    server_url = stored_state['server_url'] 
    server_name = stored_state.get('server_name', 'Figma')

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        try:
            # Figma/GitHub use Basic Auth, Notion uses client credentials in body
            auth = httpx.BasicAuth(stored_state['client_id'], stored_state['client_secret'])
           
            data = {
                "redirect_uri": stored_state['redirect_uri'],
                "code": code,
                "grant_type": "authorization_code",
            }
           
            # Add PKCE code_verifier if present (OAuth 2.1)
            if "code_verifier" in stored_state:
                data["code_verifier"] = stored_state['code_verifier']
           
            print(f"DEBUG: Sending token request to {stored_state['token_url']}")
           
            resp = await client.post(
                stored_state['token_url'], 
                data=data, 
                auth=auth,
                headers={"Accept": "application/json"}
            )
           
            print(f"DEBUG: Token response status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"DEBUG: Token response body: {resp.text}")
                logger.error(f"Token exchange failed: {resp.text}")
                raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")

            token_data = resp.json()
            
            # Calculate expiry
            import time
            expires_in = token_data.get("expires_in", 3600) # Default 1 hour
            expires_at = int(time.time()) + expires_in

            # Build credentials with expiry info
            credentials_dict = {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "expires_at": expires_at,
                "token_type": token_data.get("token_type", "Bearer")
            }
            
            import json
            credentials_json = json.dumps(credentials_dict)
            print(f"DEBUG: Token exchanged successfully. Expires at: {expires_at}")
               
        except HTTPException:
            raise # Re-raise FastAPI HTTP exceptions
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error during token exchange: {e}")
            raise HTTPException(status_code=500, detail=f"Internal error during token exchange: {e}")

    # Finalize: Store Credentials in DB column
    # Check if setting exists
    stmt = select(McpServerSetting).where(
        McpServerSetting.user_id == current_user.id,
        McpServerSetting.server_name == server_name
    )
    result = await db.execute(stmt)
    existing_setting = result.scalars().first()
    
    if existing_setting:
        existing_setting.server_url = server_url
        existing_setting.is_active = True
        existing_setting.credentials = credentials_json
        db.add(existing_setting)
    else:
        new_setting = McpServerSetting(
            user_id=current_user.id,
            server_name=server_name,
            server_url=server_url,
            is_active=True,
            description="Connected via Managed OAuth",
            credentials=credentials_json
        )
        db.add(new_setting)
        
    await db.commit()
    print("DEBUG: Saved valid credentials to DB")
    return {"status": "success", "server_url": server_url}