import json
import time
from typing import List, Dict, Optional, Any
from ..base import ConversationStorage
from ...redis.redis_client import redis_client

class RedisConversationStorage(ConversationStorage):
    """
    Redis implementation of ConversationStorage.
    Uses LangChain compatible key naming.
    """
    
    LANGCHAIN_KEY_PREFIX = "message_store:"

    async def create_new_conversation(self, user_id: int, chat_id: str, title: str) -> None:
        user_conversations_key = f"user:{user_id}:conversations"
        meta_key = f"conversation:{chat_id}:meta"
        created_at = time.time()

        with redis_client.pipeline() as pipe:
            pipe.zadd(user_conversations_key, {chat_id: created_at})
            pipe.hset(meta_key, "title", title)
            pipe.hset(meta_key, "owner_id", str(user_id))
            pipe.hset(meta_key, "created_at", created_at)
            pipe.execute()

    async def get_conversations_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        user_conversations_key = f"user:{user_id}:conversations"
        conversation_ids = redis_client.zrevrange(user_conversations_key, 0, -1)
        
        if not conversation_ids:
            return []

        pipe = redis_client.pipeline()
        for chat_id in conversation_ids:
            pipe.hget(f"conversation:{chat_id}:meta", "title")
        titles = pipe.execute()
        
        return [{"id": chat_id, "title": title} for chat_id, title in zip(conversation_ids, titles)]

    async def get_conversation_details(self, chat_id: str) -> List[Dict[str, Any]]:
        key = f"{self.LANGCHAIN_KEY_PREFIX}{chat_id}"
        message_strings = list(reversed(redis_client.lrange(key, 0, -1)))
        
        if not message_strings:
            return []
        
        messages = []
        for msg_str in message_strings:
            try:
                data = json.loads(msg_str)
                role = "user" if data.get("type") == "human" else "agent"
                content = data.get("data", {}).get("content", "")
                additional_kwargs = data.get("data", {}).get("additional_kwargs", {})
                messages.append({
                    "role": role,
                    "content": content,
                    "additional_kwargs": additional_kwargs
                })
            except (json.JSONDecodeError, TypeError):
                pass
                
        return messages

    async def get_conversation_owner(self, chat_id: str) -> Optional[str]:
        meta_key = f"conversation:{chat_id}:meta"
        return redis_client.hget(meta_key, "owner_id")

    async def get_latest_conversation_id(self, user_id: int) -> Optional[str]:
        user_conv_key = f"user:{user_id}:conversations"
        latest_id_list = redis_client.zrevrange(user_conv_key, 0, 0)
        return latest_id_list[0] if latest_id_list else None

    async def delete_conversation(self, user_id: int, chat_id: str) -> None:
        message_key = f"{self.LANGCHAIN_KEY_PREFIX}{chat_id}"
        meta_key = f"conversation:{chat_id}:meta"
        
        redis_client.zrem(f"user:{user_id}:conversations", chat_id)
        redis_client.delete(message_key, meta_key)
