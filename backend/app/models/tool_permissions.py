from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.database import Base

class ToolPermission(Base):
    """Track which tools are enabled/disabled per server per user"""
    __tablename__ = "tool_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("Users.id"), nullable=False)
    server_setting_id = Column(Integer, ForeignKey("mcp_server_settings.id"), nullable=False)
    tool_name = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="tool_permissions")
    server_setting = relationship("McpServerSetting", back_populates="tool_permissions")

    __table_args__ = (
        # Ensure one permission entry per user-server-tool combination
        {"schema": None},
    )


class ToolApproval(Base):
    """Track user approvals for tool executions"""
    __tablename__ = "tool_approvals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("Users.id"), nullable=False)
    tool_name = Column(String(255), nullable=False)
    server_name = Column(String(255), nullable=True)  # Optional: track which server
    approval_type = Column(String(20), nullable=False)  # 'once', 'always', 'never'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For session-based approvals

    # Relationships
    user = relationship("User", back_populates="tool_approvals")

    __table_args__ = (
        {"schema": None},
    )
