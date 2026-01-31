import os
import logging
from typing import Any
from functools import lru_cache

# Import implementation classes
# (Deferred imports inside function to avoid circular deps if any, though unlikely here)

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_checkpointer() -> Any:
    """
    Returns a CheckpointSaver instance based on the CHECKPOINTER_BACKEND environment variable.
    
    Supported backends:
    - 'redis' (default): Uses RedisSaver with async redis client.
    - 'memory': Uses in-memory MemorySaver (not persistent across restarts).
    - 'postgres': Placeholder for future implementation.
    
    Returns:
        BaseCheckpointSaver: An instance of a LangGraph checkpointer.
    """
    backend = os.getenv("CHECKPOINTER_BACKEND", "redis").lower().strip()
    
    logger.info(f"Initializing checkpointer with backend: {backend}")
    
    if backend == "redis":
        try:
            from .redis_checkpointer import RedisSaver
            from ..redis.redis_client import async_redis_client
            return RedisSaver(async_redis_client)
        except ImportError as e:
            logger.error(f"Failed to import Redis dependencies: {e}")
            raise
            
    elif backend == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        logger.warning("Using MemorySaver. State will NOT persist across server restarts.")
        return MemorySaver()
        
    elif backend == "postgres":
        # Placeholder for future Postgres implementation
        # This would likely use langgraph-checkpoint-postgres or a custom implementation
        logger.error("Postgres backend is not yet implemented.")
        raise NotImplementedError("Postgres checkpointer not yet implemented. Use 'redis' or 'memory'.")
        
    else:
        logger.warning(f"Unknown checkpointer backend '{backend}'. Falling back to MemorySaver.")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
