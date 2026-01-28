# models.py
from typing import Optional
from sqlalchemy import Column, String, Integer, Boolean, UniqueConstraint,ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime # You might need this for timestamps later if you add them
from ..database import database
from ..models import User
# Define the declarative base
# This is equivalent to the 'Base' from the previous example,
# but often named explicitly if you have multiple 'bases' or for clarity.


class McpServerSetting(database.Base):
    __tablename__ = "mcp_server_settings"

    id = Column(Integer, primary_key=True, index=True) # Added index for ID as well
    user_id = Column(String, ForeignKey("Users.id")) # Ensure user_id is not null
    server_name = Column(String, index=True, nullable=False)
    server_url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String, nullable=True)
    credentials = Column(String, nullable=True) # JSON string: {access_token, refresh_token, expiry, provider}
    
    # New columns for explicit auth details
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    authorization_url = Column(String, nullable=True)
    token_url = Column(String, nullable=True)
    token_url = Column(String, nullable=True)
    expires_at = Column(Integer, nullable=True) # Unix timestamp
    
    # Caching columns
    tools_manifest = Column(String, nullable=True) # JSON cache of tools list
    last_synced_at = Column(DateTime, nullable=True) # Timestamp of last refresh

    # Relationships
    tool_permissions = relationship("ToolPermission", back_populates="server_setting", cascade="all, delete-orphan")

    # Adding a unique constraint for (user_id, server_name)
    # This ensures a user cannot have two settings with the same name.
    __table_args__ = (
        UniqueConstraint('user_id', 'server_name', name='_user_server_name_uc'),
    )

    def __repr__(self):
        return f"<McpServerSetting(id={self.id}, user_id='{self.user_id}', server_name='{self.server_name}')>"


