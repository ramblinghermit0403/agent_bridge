from typing import Optional
from sqlalchemy import Column, String, Integer, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime # You might need this for timestamps later if you add them
from ..database import database

class McpServerSettingCreate(BaseModel):
    server_name: str
    server_url: str
    is_active: bool = True
    description: Optional[str] = None

# A plausible definition for McpServerSettingUpdate
# This model uses Optional fields so a PATCH request can update only specific fields
class McpServerSettingUpdate(BaseModel):
    server_name: Optional[str] = None
    server_url: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

# A plausible definition for McpServerSettingRead with id and user_id
# This Pydantic model is used for the response body.
class McpServerSettingRead(McpServerSettingCreate):
    id: int
    user_id: str

# A plausible definition for McpConnectionTestRequest
class McpConnectionTestRequest(BaseModel):
    server_url: str
