import json
import time
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
# Import the single, shared Redis client instance
from .redis_client import redis_client

# --- Key Naming Convention ---
# This is the prefix LangChain's RedisChatMessageHistory uses by default.
LANGCHAIN_KEY_PREFIX = "message_store:"

#
# user:{user_id}:conversations -> A SORTED SET (ZSET) for indexing chats
# conversation:{chat_id}:meta  -> A HASH for chat metadata (title, owner)
# message_store:{chat_id}      -> A LIST for the actual messages, managed by LangChain
#

def create_new_conversation(user_id: int, chat_id: str, title: str):
    """
    Creates metadata for a new conversation and adds it to the user's sorted list (ZSET).
    This version uses separate HSET commands for each field.
    """
    user_conversations_key = f"user:{user_id}:conversations"
    meta_key = f"conversation:{chat_id}:meta"
    created_at = time.time()

    with redis_client.pipeline() as pipe:
        pipe.zadd(user_conversations_key, {chat_id: created_at})
        
        # Individual HSET commands
        pipe.hset(meta_key, "title", title)
        pipe.hset(meta_key, "owner_id", str(user_id))
        pipe.hset(meta_key, "created_at", created_at)
        
        pipe.execute()

    print(f"Successfully created new conversation metadata for user {user_id}, chat {chat_id}")

# --- THIS FUNCTION IS NO LONGER NEEDED ---
# LangChain's `memory.aadd_message()` handles this directly and correctly.
# Keeping this function could lead to saving duplicate or inconsistent messages.
# def add_message_to_conversation(...):
#     ...


def get_conversations_for_user(user_id: int) -> List[Dict]:
    """
    Gets a list of all conversations (ID and title) for a user, sorted newest first.
    This function's logic is correct and does not need to change.
    """
    user_conversations_key = f"user:{user_id}:conversations"
    conversation_ids = redis_client.zrevrange(user_conversations_key, 0, -1)
    
    if not conversation_ids:
        return []

    pipe = redis_client.pipeline()
    for chat_id in conversation_ids:
        pipe.hget(f"conversation:{chat_id}:meta", "title")
    titles = pipe.execute()
    
    return [{"id": chat_id, "title": title} for chat_id, title in zip(conversation_ids, titles)]


# --- CORRECTED FUNCTION ---
def get_conversation_details(chat_id: str) -> List[Dict]:
    """
    Gets all messages for a specific conversation using the correct
    key prefix used by LangChain's RedisChatMessageHistory.
    """
    # Use the correct key with LangChain's default prefix
    key = f"{LANGCHAIN_KEY_PREFIX}{chat_id}"
    print("Raw messages from Redis:")

    message_strings = list(reversed(redis_client.lrange(key, 0, -1)))
    raw = redis_client.lrange(key, 0, -1)
    print("Raw messages from Redis2:", raw)
    if not message_strings:
        return []
    

    
    # We also need to parse LangChain's internal format
    messages = []
    for msg_str in message_strings:
        try:
            data = json.loads(msg_str)
            # The structure is {"type": "human/ai", "data": {"content": "...", "additional_kwargs": {...}}}
            role = "user" if data.get("type") == "human" else "agent"
            content = data.get("data", {}).get("content", "")
            additional_kwargs = data.get("data", {}).get("additional_kwargs", {})
            messages.append({
                "role": role,
                "content": content,
                "additional_kwargs": additional_kwargs
            })
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not parse message from Redis: {msg_str}. Error: {e}")
            
    return messages
    

def get_conversation_owner(chat_id: str) -> Optional[str]:
    """
    Checks who owns a conversation. Returns the user ID (as int) or None.
    This logic is correct but benefits from a type cast.
    """
    meta_key = f"conversation:{chat_id}:meta"
    owner_id_str = redis_client.hget(meta_key, "owner_id")
    return owner_id_str if owner_id_str else None


def get_latest_conversation_id(user_id: int) -> Optional[str]:
    """
    Gets the ID of the most recent conversation for a user.
    This function's logic is correct and does not need to change.
    """
    user_conv_key = f"user:{user_id}:conversations"
    latest_id_list = redis_client.zrevrange(user_conv_key, 0, 0)
    return latest_id_list[0] if latest_id_list else None


# --- CORRECTED FUNCTION ---
def delete_conversation(user_id: int, chat_id: str):
    """
    Deletes all Redis keys associated with a specific conversation for cleanup.
    """
    # 1. Remove the conversation ID from the user's sorted set.
    redis_client.zrem(f"user:{user_id}:conversations", chat_id)
    
    # 2. Define ALL keys to be deleted
    message_key = f"{LANGCHAIN_KEY_PREFIX}{chat_id}"
    meta_key = f"conversation:{chat_id}:meta"
    
    # 3. Delete all related keys in a single, efficient command.
    redis_client.delete(message_key, meta_key)


from ...models.settings import McpServerSetting # Adjust this import path as needed
from typing import Dict
from sqlalchemy.future import select
from typing import Dict
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Import your McpServerSetting model from its location
# Adjust this import path to match your project structure.
from ...models.settings import McpServerSetting 

logger = logging.getLogger(__name__)

async def get_user_servers(db: AsyncSession, user_id: str) -> Dict[str, str]:
    """
    Fetches all ACTIVE McpServerSetting records for a user from the database
    and transforms them into a dictionary suitable for the agent factory.
    
    Format: {"server_name": "server_url", ...}
    """
    logger.info(f"Fetching active MCP server settings for user_id: {user_id}")

    # 1. Create a statement to select all settings for the given user_id
    #    MODIFIED: Added a filter to only include active servers.
    statement = (
        select(McpServerSetting)
        .where(McpServerSetting.user_id == user_id)
        .where(McpServerSetting.is_active == True) # <-- IMPORTANT: Only get active servers
    )
    
    # 2. Execute the query
    result = await db.execute(statement)
    user_settings = result.scalars().all()
    
    # 3. Transform the list of model objects into a dictionary
    #    The agent will use the 'server_name' from your DB as part of the tool name.
    server_dict = {setting.server_name: setting.server_url for setting in user_settings}
    
    if server_dict:
        logger.info(f"Found {len(server_dict)} active servers for user {user_id}: {list(server_dict.keys())}")
    else:
        logger.info(f"No active MCP servers found for user {user_id}.")

    return server_dict