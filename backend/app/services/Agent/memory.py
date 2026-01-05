import os
from langchain_community.chat_message_histories import RedisChatMessageHistory

def get_session_memory(session_id: str) -> RedisChatMessageHistory:
    """Creates a Redis-backed memory object for a given session_id."""
    redis_url = os.getenv("REDIS_URL_MEMORY", "redis://localhost:6379/1")
    return RedisChatMessageHistory(session_id=session_id, url=redis_url)
