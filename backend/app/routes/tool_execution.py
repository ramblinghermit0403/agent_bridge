from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from ..database.database import get_db
from ..auth.oauth2 import get_current_user
from ..models import User
from ..services.tool_permissions_helper import PendingApproval, save_tool_approval

router = APIRouter(prefix="/api/tool-execution", tags=["tool-execution"])


class ApprovalRequest(BaseModel):
    approval_id: str
    approved: bool
    approval_type: str | None = None  # 'once' or 'always'


class ApprovalStatusResponse(BaseModel):
    approval_id: str
    status: str  # 'pending', 'approved', 'denied'
    approval_type: str | None = None


@router.post("/approve")
async def approve_tool_execution(
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or deny a pending tool execution.
    """
    pending = PendingApproval.get(request.approval_id)
    
    if not pending:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if pending['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if request.approved:
        PendingApproval.approve(request.approval_id, request.approval_type or 'once')
        
        # Save approval preference if 'always'
        if request.approval_type == 'always':
            await save_tool_approval(
                db,
                user_id=current_user.id,
                tool_name=pending['tool_name'],
                approval_type='always',
                server_name=pending['server_name']
            )
    else:
        PendingApproval.deny(request.approval_id)
    
    return {"message": "Approval processed", "approved": request.approved}


@router.get("/status/{approval_id}", response_model=ApprovalStatusResponse)
async def get_approval_status(
    approval_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check the status of a pending approval.
    """
    pending = PendingApproval.get(approval_id)
    
    if not pending:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if pending['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if pending['approved'] is None:
        status = 'pending'
    elif pending['approved']:
        status = 'approved'
    else:
        status = 'denied'
    
    return ApprovalStatusResponse(
        approval_id=approval_id,
        status=status,
        approval_type=pending.get('approval_type')
    )
