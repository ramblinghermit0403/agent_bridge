from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class ConversationStorage(ABC):
    """
    Abstract base class for conversation storage backends.
    Implement this to support other backends like Postgres, Mongo, or Filesystem.
    """

    @abstractmethod
    async def create_new_conversation(self, user_id: int, chat_id: str, title: str) -> None:
        """Initialize a new conversation with metadata."""
        pass

    @abstractmethod
    async def get_conversations_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """List all conversations for a user (id and title)."""
        pass

    @abstractmethod
    async def get_conversation_details(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific conversation."""
        pass
    
    @abstractmethod
    async def get_conversation_owner(self, chat_id: str) -> Optional[str]:
        """Return the user_id that owns this conversation."""
        pass

    @abstractmethod
    async def get_latest_conversation_id(self, user_id: int) -> Optional[str]:
        """Get the ID of the most recent conversation."""
        pass

    @abstractmethod
    async def delete_conversation(self, user_id: int, chat_id: str) -> None:
        """Delete a conversation and all its messages."""
        pass
