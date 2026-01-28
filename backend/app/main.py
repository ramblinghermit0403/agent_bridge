from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, Request
import nest_asyncio
from .routes import agent,auth,user,settings,tool_permissions,tool_execution,providers
from fastapi.middleware.cors import CORSMiddleware
from .database import database
from contextlib import asynccontextmanager



# Models creation
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles all startup and shutdown events for the application.
    This replaces all deprecated 'on_event("startup")' and 'on_event("shutdown")' handlers.
    """
    # --- Code to run ON STARTUP ---
    print("Lifespan: Server is starting up...")

    # 1. Clear LLM Caches to ensure fresh API keys
    from .services.agent.llm_factory import get_llm
    get_llm.cache_clear()
    print("✅ LLM Factory cache cleared.")

    # 2. Create database tables
    print("Lifespan: Initializing database tables...")
    try:
        async with database.engine.begin() as conn:
            await conn.run_sync(database.Base.metadata.create_all)
        print("✅ Database tables initialized successfully.")
    except Exception as e:
        print(f"❌ Error during database table initialization: {e}")
        # It's crucial to re-raise the exception here to prevent the application
        # from starting if the database setup fails.
        raise

    # 3. Background: Refresh Tool Manifests
    async def refresh_all_tool_manifests():
        from .routes.settings import _refresh_manifest_internal
        from .models.settings import McpServerSetting
        from sqlalchemy import select
        from .database import database
        
        print("🔄 Background: Starting tool manifest refresh...")
        try:
            async with database.AsyncSessionLocal() as db:
                stmt = select(McpServerSetting).where(McpServerSetting.is_active == True)
                result = await db.execute(stmt)
                settings = result.scalars().all()
                
                for setting in settings:
                    print(f"   - Refreshing tools for: {setting.server_name}")
                    # We need a user object for _refresh_manifest_internal, but it only uses user-context logging.
                    class DummyUser: id="startup-system"
                    
                    try:
                        await _refresh_manifest_internal(setting.id, db, DummyUser())
                    except Exception as e:
                        print(f"   ❌ Failed to refresh {setting.server_name}: {e}")
                        
        except Exception as e:
            print(f"❌ Error during background manifest refresh: {e}")
        print("✅ Background: Tool manifest refresh complete.")

    import asyncio
    refresh_task = asyncio.create_task(refresh_all_tool_manifests())

    # The 'yield' keyword marks the point where the application starts serving requests.
    yield

    # --- Code to run ON SHUTDOWN ---
    print("Lifespan: Server is shutting down...")
    
    # Cancel background task
    if refresh_task and not refresh_task.done():
        print("Lifespan: Cancelling background refresh task...")
        refresh_task.cancel()
        try:
            # Wait with a timeout
            await asyncio.wait_for(refresh_task, timeout=2.0)
        except Exception:
            # Swallow ALL errors during shutdown cancellation to prevent "RuntimeError: cancel scope" noise.
            # This is harmless as the server is dying anyway.
            pass
            
    print("Lifespan: Server shutdown complete.")


app = FastAPI(lifespan=lifespan)

# Include the agent router
app.include_router(agent.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(user.router)
app.include_router(settings.router)
app.include_router(tool_permissions.router)
app.include_router(tool_execution.router)
app.include_router(providers.router)


# CORS middleware configuration
# CORS middleware configuration
import os
origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
