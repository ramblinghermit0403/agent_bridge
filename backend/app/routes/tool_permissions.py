from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
from pydantic import BaseModel
from ..database.database import get_db
from ..models import ToolPermission, ToolApproval, McpServerSetting
from ..auth.oauth2 import get_current_user
from ..models.User import User
import httpx
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["tool-permissions"])


# Pydantic models for request/response
class ToolInfo(BaseModel):
    name: str
    description: str | None = None
    is_enabled: bool = True


class ToolToggleRequest(BaseModel):
    is_enabled: bool


class ToolApprovalRequest(BaseModel):
    tool_name: str
    server_name: str | None = None
    approval_type: str  # 'once', 'always', 'never'


class ToolApprovalResponse(BaseModel):
    id: int
    tool_name: str
    server_name: str | None
    approval_type: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/mcp/settings/{server_id}/tools", response_model=List[ToolInfo])
async def get_server_tools(
    server_id: int,

    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tools for a specific MCP server with their enabled status.
    """
    # Verify server belongs to user
    result = await db.execute(
        select(McpServerSetting).filter(
            McpServerSetting.id == server_id,
            McpServerSetting.user_id == current_user.id
        )
    )
    server_setting = result.scalars().first()
    
    if not server_setting:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Fetch tools from the MCP server
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{server_setting.server_url}/tools",
                timeout=10.0
            )
            response.raise_for_status()
            tools_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tools from server: {str(e)}")
    
    # Get user's tool permissions

    result = await db.execute(
        select(ToolPermission).filter(
            ToolPermission.user_id == current_user.id,
            ToolPermission.server_setting_id == server_id
        )
    )
    permissions = result.scalars().all()
    
    permission_map = {p.tool_name: p.is_enabled for p in permissions}
    
    # Combine tools with permission status
    result = []
    for tool in tools_data.get("tools", []):
        tool_name = tool.get("name")
        result.append(ToolInfo(
            name=tool_name,
            description=tool.get("description"),
            is_enabled=permission_map.get(tool_name, True)  # Default to enabled
        ))
    
    return result


@router.patch("/mcp/settings/{server_id}/tools/{tool_name}")
async def toggle_tool(
    server_id: int,
    tool_name: str,
    request: ToolToggleRequest,

    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle a tool's enabled/disabled status.
    """
    # Verify server belongs to user
    result = await db.execute(
        select(McpServerSetting).filter(
            McpServerSetting.id == server_id,
            McpServerSetting.user_id == current_user.id
        )
    )
    server_setting = result.scalars().first()
    
    if not server_setting:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Find or create tool permission
    result = await db.execute(
        select(ToolPermission).filter(
            ToolPermission.user_id == current_user.id,
            ToolPermission.server_setting_id == server_id,
            ToolPermission.tool_name == tool_name
        )
    )
    permission = result.scalars().first()
    
    if permission:
        permission.is_enabled = request.is_enabled
        permission.updated_at = datetime.utcnow()
    else:
        permission = ToolPermission(
            user_id=current_user.id,
            server_setting_id=server_id,
            tool_name=tool_name,
            is_enabled=request.is_enabled
        )
        db.add(permission)
    
    await db.commit()
    await db.refresh(permission)
    
    return {"message": f"Tool {tool_name} {'enabled' if request.is_enabled else 'disabled'}", "is_enabled": permission.is_enabled}


@router.get("/tool-approvals", response_model=List[ToolApprovalResponse])
async def get_tool_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tool approval preferences for the current user.
    """
    result = await db.execute(
        select(ToolApproval).filter(
            ToolApproval.user_id == current_user.id
        )
    )
    approvals = result.scalars().all()
    
    return approvals


@router.post("/tool-approvals", response_model=ToolApprovalResponse)
async def create_tool_approval(
    request: ToolApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update a tool approval preference.
    """
    # Check if approval already exists
    result = await db.execute(
        select(ToolApproval).filter(
            ToolApproval.user_id == current_user.id,
            ToolApproval.tool_name == request.tool_name
        )
    )
    approval = result.scalars().first()
    
    if approval:
        # Update existing
        approval.approval_type = request.approval_type
        approval.server_name = request.server_name
        approval.created_at = datetime.utcnow()
        
        # Set expiry for 'once' approvals (expires in 1 hour)
        if request.approval_type == "once":
            approval.expires_at = datetime.utcnow() + timedelta(hours=1)
        else:
            approval.expires_at = None
    else:
        # Create new
        approval = ToolApproval(
            user_id=current_user.id,
            tool_name=request.tool_name,
            server_name=request.server_name,
            approval_type=request.approval_type,
            expires_at=datetime.utcnow() + timedelta(hours=1) if request.approval_type == "once" else None
        )
        db.add(approval)
    
    await db.commit()
    await db.refresh(approval)
    
    return approval


@router.delete("/tool-approvals/{tool_name}")
async def delete_tool_approval(
    tool_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a tool approval preference.
    """
    result = await db.execute(
        select(ToolApproval).filter(
            ToolApproval.user_id == current_user.id,
            ToolApproval.tool_name == tool_name
        )
    )
    approval = result.scalars().first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    await db.delete(approval)
    await db.commit()
    
    return {"message": f"Approval for {tool_name} removed"}
