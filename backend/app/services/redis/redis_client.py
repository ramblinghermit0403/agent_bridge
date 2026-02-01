import redis
import os
import sys

# --- Configuration ---
# Prioritize REDIS_URL or REDIS_URL_MEMORY
REDIS_URL = os.getenv("REDIS_URL", os.getenv("REDIS_URL_MEMORY"))

try:
    if REDIS_URL:
        # Create client from URL
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        
        # Extract details for logging
        conn_kwargs = redis_client.connection_pool.connection_kwargs
        REDIS_HOST = conn_kwargs.get("host")
        REDIS_PORT = conn_kwargs.get("port")
        REDIS_DB = conn_kwargs.get("db")
    else:
        # Fallback to individual variables
        REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_DB = int(os.getenv("REDIS_DB", 1))

        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
    
    # Check if the connection is successful when the app starts.
    redis_client.ping()
    print(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT} on DB {REDIS_DB}.")

    # --- Async Client Instance ---
    import redis.asyncio as aioredis
    
    if REDIS_URL:
         async_redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    else:
        async_redis_client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

except Exception as e:
    print(f"FATAL: Could not connect to Redis. Error: {e}", file=sys.stderr)
    sys.exit(1)