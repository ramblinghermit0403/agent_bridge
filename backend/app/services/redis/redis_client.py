import redis
import os
import sys

# --- Configuration ---
# Read connection details from environment variables for flexibility.
# Provide sensible defaults for local development.
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# Use DB 1 as you requested.
REDIS_DB = int(os.getenv("REDIS_DB", 1))

# --- The Client Instance ---
# This is the single, direct Redis client instance for your application.
# `decode_responses=True` is CRUCIAL. It ensures that data read from Redis
# is automatically converted from bytes to standard Python strings.
try:
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
    async_redis_client = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )
    # We can't easily ping here because we are in top-level sync code, 
    # but the settings are the same as the sync client.

except redis.exceptions.ConnectionError as e:
    print(f"FATAL: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Please ensure it is running.", file=sys.stderr)
    print(f"Error details: {e}", file=sys.stderr)
    # Exit the application if Redis is not available, as it's a critical service.
    sys.exit(1)