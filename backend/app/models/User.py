from ..database import database
from sqlalchemy import Integer,Column,String,BigInteger,TIMESTAMP,func,Boolean, ForeignKey,DateTime,UniqueConstraint,JSON
from datetime import datetime
from sqlalchemy import Index, text
from sqlalchemy.orm import relationship


# user model

class User(database.Base):
    """
    Represents a registered user or guest in the system.

    Attributes:
        id (str): Unique identifier for the user (PK).
        username (str, optional): Display name for registered users.
        email (str, optional): Contact email for registered users.
        is_guest (bool): Flag indicating if the user is a temporary guest account.
        tool_permissions (list[ToolPermission]): Linked tool permissions.
        tool_approvals (list[ToolApproval]): Linked tool execution approvals.
    """
    __tablename__="Users"
    id=Column(String, primary_key=True)
    username=Column(String, nullable=True) # Username optional for guest
    email=Column(String, nullable=True)    # Email optional for guest
    password_hash=Column(String, nullable=True) # Password optional for guest
    is_guest=Column(Boolean, default=False)

    # Relationships
    tool_permissions = relationship("ToolPermission", back_populates="user", cascade="all, delete-orphan")
    tool_approvals = relationship("ToolApproval", back_populates="user", cascade="all, delete-orphan")

