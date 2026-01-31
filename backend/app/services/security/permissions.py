"""
Helper functions for tool permission checking and approval management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import ToolPermission, ToolApproval
from datetime import datetime
import uuid


class PendingApproval:
    """Stores pending approval requests"""
    _pending = {}
    
    @classmethod
    def create(cls, user_id: str, tool_name: str, server_name: str, tool_input: dict, approval_id: str = None) -> str:
        """Create a new pending approval request. Deduplicates existing pending requests."""
        # 1. Check for existing pending request (Deduplication)
        for pid, data in cls._pending.items():
            if (data['user_id'] == user_id and 
                data['tool_name'] == tool_name and 
                data['approved'] is None):
                # We could checks tool_input equality too, but for safety/simplicity, 
                # blocking the same tool for the same user is usually enough dedupe 
                # for the immediate timeframe. 
                # Let's check input roughly to allow different args.
                if data['tool_input'] == tool_input:
                    # Update timestamp to keep it fresh
                    data['created_at'] = datetime.utcnow()
                    print(f"DEBUG: PendingApproval DEDUPLICATED existing {pid} for {tool_name}")
                    return pid

        if not approval_id:
            approval_id = str(uuid.uuid4())
            
        cls._pending[approval_id] = {
            'user_id': user_id,
            'tool_name': tool_name,
            'server_name': server_name,
            'tool_input': tool_input,
            'approved': None,  # None = pending, True = approved, False = denied
            'approval_type': None,  # 'once' or 'always'
            'created_at': datetime.utcnow() # Add timestamp for filtering stale requests
        }
        print(f"DEBUG: PendingApproval CREATED {approval_id} for {tool_name}")
        return approval_id
    
    @classmethod
    def get(cls, approval_id: str):
        """Get a pending approval"""
        return cls._pending.get(approval_id)
    
    @classmethod
    def approve(cls, approval_id: str, approval_type: str = 'once'):
        """Approve a pending request"""
        if approval_id in cls._pending:
            cls._pending[approval_id]['approved'] = True
            cls._pending[approval_id]['approval_type'] = approval_type
            print(f"DEBUG: PendingApproval APPROVED {approval_id}")
        else:
            print(f"DEBUG: PendingApproval APPROVED failed - {approval_id} not found")
    
    @classmethod
    def deny(cls, approval_id: str):
        """Deny a pending request"""
        if approval_id in cls._pending:
            cls._pending[approval_id]['approved'] = False
            print(f"DEBUG: PendingApproval DENIED {approval_id}")
        else:
            print(f"DEBUG: PendingApproval DENY failed - {approval_id} not found")
    
    @classmethod
    def remove(cls, approval_id: str):
        """Remove a pending approval"""
        if approval_id in cls._pending:
            cls._pending.pop(approval_id, None)
            print(f"DEBUG: PendingApproval REMOVED {approval_id}")


async def check_tool_permission(db: AsyncSession, user_id: str, server_setting_id: int, tool_name: str) -> bool:
    """
    Check if a tool is enabled for the user.
    Returns True if enabled (or no permission record exists - default enabled).
    """
    result = await db.execute(
        select(ToolPermission).filter(
            ToolPermission.user_id == user_id,
            ToolPermission.server_setting_id == server_setting_id,
            ToolPermission.tool_name == tool_name
        )
    )
    permission = result.scalars().first()
    
    if permission is None:
        return True  # Default to enabled if no permission record
    
    return permission.is_enabled


async def check_tool_approval(db: AsyncSession, user_id: str, tool_name: str) -> tuple[bool, str | None]:
    """
    Check if user has a standing approval for this tool.
    Returns (needs_approval, approval_type)
    - needs_approval: True if user approval is required
    - approval_type: 'always' if pre-approved, None otherwise
    """
    # Whitelist internal LangChain tools (like _Exception)
    if tool_name.startswith("_"):
        return False, 'always'

    result = await db.execute(
        select(ToolApproval).filter(
            ToolApproval.user_id == user_id,
            ToolApproval.tool_name == tool_name
        )
    )
    approval = result.scalars().first()
    
    if approval is None:
        return True, None  # Needs approval, no standing approval
    
    # Check if approval has expired
    if approval.expires_at and approval.expires_at < datetime.utcnow():
        await db.delete(approval)
        await db.commit()
        return True, None
    
    if approval.approval_type == 'always':
        return False, 'always'  # No approval needed
    elif approval.approval_type == 'never':
        return True, 'never'  # Always deny
    
    return True, None  # Needs approval for 'once' or other types


async def save_tool_approval(db: AsyncSession, user_id: str, tool_name: str, approval_type: str, server_name: str = None):
    """
    Save a tool approval preference.
    """
    from datetime import timedelta
    
    # Check if approval already exists
    result = await db.execute(
        select(ToolApproval).filter(
            ToolApproval.user_id == user_id,
            ToolApproval.tool_name == tool_name
        )
    )
    approval = result.scalars().first()
    
    if approval:
        approval.approval_type = approval_type
        approval.server_name = server_name
        approval.created_at = datetime.utcnow()
        
        if approval_type == 'once':
            approval.expires_at = datetime.utcnow() + timedelta(hours=1)
        else:
            approval.expires_at = None
    else:
        approval = ToolApproval(
            user_id=user_id,
            tool_name=tool_name,
            server_name=server_name,
            approval_type=approval_type,
            expires_at=datetime.utcnow() + timedelta(hours=1) if approval_type == 'once' else None
        )
        db.add(approval)
    
    await db.commit()
    await db.refresh(approval)
    return approval
