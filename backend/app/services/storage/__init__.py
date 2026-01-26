from .base import ConversationStorage
from .providers.redis import RedisConversationStorage
import os

# Factory to get the configured storage backend
# In the future, this could read from os.getenv("STORAGE_BACKEND")
def get_storage_client() -> ConversationStorage:
    return RedisConversationStorage()

# Singleton instance for easy import
storage_client = get_storage_client()
