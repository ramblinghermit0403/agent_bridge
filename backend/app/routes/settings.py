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
    current_user: User.User = Depends(get_current_user),
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
    current_user: User.User = Depends(get_current_user),
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

# Route to update an MCP server setting
@router.patch("/api/mcp/settings/{setting_id}", response_model=McpServerSettingRead)
async def update_mcp_setting(
    setting_id: int,
    setting_update: McpServerSettingUpdate,
    current_user: User.User = Depends(get_current_user),
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
    current_user: User.User = Depends(get_current_user),
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
    current_user: User.User = Depends(get_current_user),
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

    return current_user