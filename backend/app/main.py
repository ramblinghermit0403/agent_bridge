from fastapi import FastAPI, Request
import nest_asyncio
from .routes import agent,auth,user,settings
from fastapi.middleware.cors import CORSMiddleware
from .database import database
from contextlib import asynccontextmanager
from .services.Agent import langchain_agent


# Models creation
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles all startup and shutdown events for the application.
    This replaces all deprecated 'on_event("startup")' and 'on_event("shutdown")' handlers.
    """
    # --- Code to run ON STARTUP ---
    print("Lifespan: Server is starting up...")

    # 1. Create database tables
    print("Lifespan: Initializing database tables...")
    try:
        async with database.engine.begin() as conn:
            await conn.run_sync(database.Base.metadata.create_all)
        print("✅ Database tables initialized successfully.")

            # 3. Create the LangChain Agent
        # print("Lifespan: Initializing LangChain agent...")
        # # The agent is created once and stored in app.state, making it available
        # # to all routers via dependency injection.
        # app.state.agent_with_memory = await langchain_agent.create_final_agent_pipeline()
        # print("✅ LangChain agent initialized.")
    except Exception as e:
        print(f"❌ Error during database table initialization: {e}")
        # It's crucial to re-raise the exception here to prevent the application
        # from starting if the database setup fails.
        raise

    # The 'yield' keyword marks the point where the application starts serving requests.
    yield

    # --- Code to run ON SHUTDOWN ---
    print("Lifespan: Server is shutting down...")
    # Add any cleanup code here, e.g., closing external connections, releasing resources.
    # For SQLAlchemy, typically the engine and sessions are managed automatically,
    # but if you have custom resource pools or connections, close them here.
    print("Lifespan: Server shutdown complete.")


app = FastAPI(lifespan=lifespan)

# Include the agent router
app.include_router(agent.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(settings.router)


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
