import pickle
import logging
from typing import Any, AsyncIterator, Dict, Optional, Tuple, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple, WRITES_IDX_MAP
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class RedisSaver(BaseCheckpointSaver):
    """
    A checkpoint saver that stores checkpoints in Redis.
    """
    
    def __init__(self, client: Redis):
        super().__init__()
        self.client = client

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """
        Get a checkpoint tuple from the store.
        """
        thread_id = config["configurable"]["thread_id"]
        user_id = config["configurable"].get("user_id")
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        if checkpoint_id:
            key = f"checkpoint:{user_id}:{thread_id}:{checkpoint_id}" if user_id else f"checkpoint:{thread_id}:{checkpoint_id}"
        else:
            # Get the latest checkpoint from history
            history_key = f"thread:{user_id}:{thread_id}:history" if user_id else f"thread:{thread_id}:history"
            result = await self.client.zrevrange(history_key, 0, 0)
            if not result:
                return None
            checkpoint_id = result[0].decode('utf-8') if isinstance(result[0], bytes) else result[0]
            key = f"checkpoint:{user_id}:{thread_id}:{checkpoint_id}" if user_id else f"checkpoint:{thread_id}:{checkpoint_id}"

        # Fetch the actual checkpoint data
        data = await self.client.get(key)
        if not data:
            return None
            
        # Deserialize checkpoint
        import base64
        import pickle
        try:
            stored_bytes = base64.b64decode(data.encode('utf-8'))
            stored_data = pickle.loads(stored_bytes)
            
            checkpoint = stored_data["checkpoint"]
            metadata = stored_data["metadata"]
            parent_config = stored_data.get("parent_config")
            
            # Retrieve pending writes
            writes_key = f"checkpoint:{user_id}:{thread_id}:{checkpoint_id}:writes" if user_id else f"checkpoint:{thread_id}:{checkpoint_id}:writes"
            raw_writes = await self.client.hgetall(writes_key)
            pending_writes = []
            
            if raw_writes:
                for field, val_b64 in raw_writes.items():
                    try:
                        val_bytes = base64.b64decode(val_b64)
                        # We stored (task_id, channel, val_b64_str, task_path)
                        # But wait, in aput_writes below I'm planning to store (task_id, channel, val_b64_str, task_path)
                        # So deserializing the tuple first
                        task_id, channel, val_b64_inner, _ = pickle.loads(val_bytes)
                        
                        # Now deserialize the actual value
                        val_inner_bytes = base64.b64decode(val_b64_inner)
                        value = pickle.loads(val_inner_bytes)
                        
                        pending_writes.append((task_id, channel, value))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize write {field}: {e}")
            
            return CheckpointTuple(
                config=config, 
                checkpoint=checkpoint, 
                metadata=metadata, 
                parent_config=parent_config,
                pending_writes=pending_writes
            )
        except Exception as e:
            logger.error(f"Failed to deserialize checkpoint {key}: {e}")
            return None

    async def alist(
        self,
        config: RunnableConfig,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: int = 15,
    ) -> AsyncIterator[CheckpointTuple]:
        """
        List checkpoints for a given thread.
        """
        thread_id = config["configurable"]["thread_id"]
        user_id = config["configurable"].get("user_id")
        history_key = f"thread:{user_id}:{thread_id}:history" if user_id else f"thread:{thread_id}:history"
        
        checkpoint_ids = await self.client.zrevrange(history_key, 0, limit - 1)
        
        for cp_id_bytes in checkpoint_ids:
            cp_id = cp_id_bytes.decode('utf-8') if isinstance(cp_id_bytes, bytes) else cp_id_bytes
            
            if before and before["configurable"].get("checkpoint_id") == cp_id:
                continue

            key = f"checkpoint:{user_id}:{thread_id}:{cp_id}" if user_id else f"checkpoint:{thread_id}:{cp_id}"
            data = await self.client.get(key)
            if data:
                try:
                    import base64
                    import pickle
                    stored_bytes = base64.b64decode(data.encode('utf-8'))
                    stored_data = pickle.loads(stored_bytes)
                    
                    # Retrieve pending writes
                    writes_key = f"checkpoint:{user_id}:{thread_id}:{cp_id}:writes" if user_id else f"checkpoint:{thread_id}:{cp_id}:writes"
                    raw_writes = await self.client.hgetall(writes_key)
                    pending_writes = []
                    
                    if raw_writes:
                        for field, val_b64 in raw_writes.items():
                            try:
                                val_bytes = base64.b64decode(val_b64)
                                task_id, channel, val_b64_inner, _ = pickle.loads(val_bytes)
                                val_inner_bytes = base64.b64decode(val_b64_inner)
                                value = pickle.loads(val_inner_bytes)
                                pending_writes.append((task_id, channel, value))
                            except Exception:
                                pass
                    
                    yield CheckpointTuple(
                        config={"configurable": {"thread_id": thread_id, "checkpoint_id": cp_id}},
                        checkpoint=stored_data["checkpoint"],
                        metadata=stored_data["metadata"],
                        parent_config=stored_data.get("parent_config"),
                        pending_writes=pending_writes
                    )
                except Exception:
                    pass

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Dict[str, Any],
    ) -> RunnableConfig:
        """
        Save a checkpoint to the store.
        """
        thread_id = config["configurable"]["thread_id"]
        user_id = config["configurable"].get("user_id")
        checkpoint_id = checkpoint["id"]
        
        key = f"checkpoint:{user_id}:{thread_id}:{checkpoint_id}" if user_id else f"checkpoint:{thread_id}:{checkpoint_id}"
        history_key = f"thread:{user_id}:{thread_id}:history" if user_id else f"thread:{thread_id}:history"
        
        # Sanitize config to remove unpicklable objects (like tool_registry)
        sanitized_config = config.copy()
        if "configurable" in sanitized_config:
            # Create a shallow copy of configurable to modify it without affecting the original
            sanitized_config["configurable"] = sanitized_config["configurable"].copy()
            # Remove keys known to contain unpicklable objects
            if "tool_registry" in sanitized_config["configurable"]:
                del sanitized_config["configurable"]["tool_registry"]

        # Sanitize config to remove unpicklable objects (like tool_registry and callbacks)
        sanitized_config = config.copy()
        
        # Remove callbacks (runtime objects, not picklable)
        if "callbacks" in sanitized_config:
             del sanitized_config["callbacks"]

        if "configurable" in sanitized_config:
            # Create a shallow copy of configurable to modify it without affecting the original
            sanitized_config["configurable"] = sanitized_config["configurable"].copy()
            # Remove keys known to contain unpicklable objects
            if "tool_registry" in sanitized_config["configurable"]:
                del sanitized_config["configurable"]["tool_registry"]

        data = {
            "checkpoint": checkpoint,
            "metadata": metadata,
            "parent_config": sanitized_config
        }
        
        # Serialize
        import base64
        # pickle.dumps returns bytes. we b64encode it to bytes, then decode to str to store in text-mode redis
        try:
             serialized_bytes = pickle.dumps(data)
        except TypeError as e:
             logger.error(f"Failed to pickle checkpoint data: {e}. Keys: {list(data.keys())}")
             # We should probably raise here or handle gracefully, raising prevents silent data loss
             raise e

        serialized_b64 = base64.b64encode(serialized_bytes).decode('utf-8')
        
        # We assume strict ordering by time is sufficient for zadd score in this simplified version
        # Or we can use timestamp from metadata if available, but time.time() is fine for unique-ing order
        import time
        score = time.time()
        
        async with self.client.pipeline() as pipe:
            pipe.set(key, serialized_b64)
            pipe.zadd(history_key, {checkpoint_id: score})
            # Optional: Expire old checkpoints after some time?
            await pipe.execute()
            
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Save a list of writes to the store."""
        thread_id = config["configurable"]["thread_id"]
        user_id = config["configurable"].get("user_id")
        checkpoint_id = config["configurable"]["checkpoint_id"]
        
        writes_key = f"checkpoint:{user_id}:{thread_id}:{checkpoint_id}:writes" if user_id else f"checkpoint:{thread_id}:{checkpoint_id}:writes"
        
        import pickle
        import base64
        
        async with self.client.pipeline() as pipe:
            for idx, (channel, value) in enumerate(writes):
                 # Serialize value
                 try:
                     val_bytes = pickle.dumps(value)
                     val_b64 = base64.b64encode(val_bytes).decode('utf-8')
                 except Exception as e:
                     logger.error(f"Failed to pickle write {channel}: {e}")
                     continue
                 
                 key_idx = WRITES_IDX_MAP.get(channel, idx)
                 field = f"{task_id}:{key_idx}"
                 
                 # Store tuple: (task_id, channel, val_b64, task_path)
                 storage_tuple = (task_id, channel, val_b64, task_path)
                 storage_bytes = pickle.dumps(storage_tuple)
                 storage_b64 = base64.b64encode(storage_bytes).decode('utf-8')
                 
                 pipe.hset(writes_key, field, storage_b64)
                 
            await pipe.execute()
