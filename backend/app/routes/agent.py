import uuid
import os
import json
import logging
from typing import Optional, Any, AsyncGenerator, List, Dict # Added List, Dict
from datetime import datetime

from fastapi import status, APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

# LangChain specific imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, GoogleAPICallError


# --- Your Project's Local Imports ---
from ..services.redis.redis_client import redis_client # Still needed for simple key checks if any
from ..services.storage import storage_client as crud_storage
# from ..services.redis import crud_redis # DEPRECATED
from ..database import database
from ..auth.oauth2 import get_current_user
from ..models import User
from ..services.security.permissions import check_tool_permission, check_tool_approval, PendingApproval
import asyncio

# --- MODIFIED: Import the parameterized agent factory, not the global one ---
from app.services.agent.agent_factory import get_session_memory, get_llm
from ..services.agent_manager import get_or_create_agent
# --- NEW: Import for fetching user-specific data ---
from app.services.mcp.config import get_user_servers

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models (Unchanged) ---
class AskRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = Field(None)

class AskResponse(BaseModel):
    output: str
    user_id: str
    session_id: str

# --- Create the Router Instance ---
router = APIRouter(tags=['Agent'])

# --- MODIFIED: The SSE Streaming API Route ---
@router.get("/ask/stream")
async def ask_agent_stream(
    fastapi_request: Request,
    token: str = Query(...),
    prompt: str = Query(..., min_length=1),
    session_id: Optional[str] = Query(None),
    model_provider: str = Query("gemini"), # new param
    model: str = Query("gemini-2.5-flash"), # new param, renamed from model_name for cleaner URL
    resume: bool = Query(False), # New param for resuming interrupted sessions
    db: AsyncSession = Depends(database.get_db),
) -> EventSourceResponse:
    """
    Handles a user's prompt by building a user-specific agent on-the-fly,
    streaming the output, and managing conversation history.
    """
    current_user: User = await get_current_user(token, db)
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # --- NEW: On-Demand Agent Creation ---
    # 1. Fetch this user's specific server configurations from the database.
    user_servers = await get_user_servers(db, user_id=current_user.id)
    
    # The rest of your code works as-is, now using the locally created `agent_executor`
    actual_session_id = session_id or str(uuid.uuid4())
    user_id = current_user.id
    hybrid_session_key = f"{actual_session_id}"

    is_new_chat = not redis_client.exists(f"conversation:{actual_session_id}:meta")
    if is_new_chat:
        title = prompt[:35] + "..." if len(prompt) > 35 else prompt
        await crud_storage.create_new_conversation(user_id=user_id, chat_id=actual_session_id, title=title)

    memory = get_session_memory(hybrid_session_key)
    if memory is None:
        raise HTTPException(status_code=503, detail="Conversation memory service is unavailable.")

    # Get history BEFORE adding the new message to avoid duplication in the prompt
    chat_history = await memory.aget_messages()

    # Only add message if NOT resuming
    if not resume:
        memory.add_user_message(prompt)
        
    # Formatter removed for client-side markdown rendering optimization
    # formatter_prompt = build_formatter_prompt()
    # llm_formatter = get_llm(model_provider=model_provider, model_name=model)
    # formatter_chain = formatter_prompt | llm_formatter | StrOutputParser()

    # 2. Get cached or create new agent
    try:
        agent_executor, is_cache_hit = await get_or_create_agent(
            user_id=current_user.id, 
            user_servers=user_servers,
            model_provider=model_provider,
            model_name=model
        )
    except Exception as e:
        logger.error(f"Failed to create agent pipeline for user {current_user.id}: {e}", exc_info=True)
        # We can't yield error in EventSource here easily if we crash before returning response,
        # but for an HTTP handler raising exception is fine.
        raise HTTPException(status_code=500, detail="Failed to initialize agent pipeline.")

    # 3. Stream Events using the new Service
    from ..services.streaming import stream_agent_events
    
    agent_input = {"input": prompt, "chat_history": chat_history} if not resume else {}
    config = {"configurable": {"user_id": user_id, "thread_id": actual_session_id}}
    
    # Notify user of start (if not resuming, although the service handles some notifications, 
    # we can yield an initial event here if strictly necessary, but the service works better)
    
    return EventSourceResponse(
        stream_agent_events(
            agent_executor=agent_executor,
            agent_input=agent_input,
            config=config,
            session_id=actual_session_id,
            user_id=user_id,
            resume=resume
        ),
        media_type="text/event-stream"
    )



# --- UNCHANGED: Your other routes for managing chat history are fine ---

@router.get("/api/chats/", response_model=List[Dict])
async def read_conversations_for_user(
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Fetching conversation history for user_id: {current_user.id}")
    return await crud_storage.get_conversations_for_user(user_id=current_user.id)

@router.get("/api/chats/{chat_id}")
async def read_conversation_messages(
    chat_id: str,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Fetching messages for chat_id: {chat_id} for user_id: {current_user.id}")
    owner_id = await crud_storage.get_conversation_owner(chat_id)
    if owner_id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # owner_id from redis is string, current_user.id is uuid or str. storage returns str.
    if str(owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    
    messages = await crud_storage.get_conversation_details(chat_id)
    # We need to fetch title from meta separately if not included in details, 
    # but the current impl of get_conversations return it. 
    # Let's check redis directly for title or add get_title method.
    # For now, let's just reuse basic redis call inside the route or add get_meta to storage.
    # Simplest is to assume storage handles it or just expose redis_client for non-generic ops if needed.
    # But to be clean, let's use the list to find title or just fetch title directly.
    # Actually, the original code used redis_client.hget directly. 
    # Ideally we should add `get_conversation_title` to interface. 
    # For now, I will assume we can rely on `redis_client` for this specific metadata OR update interface.
    # Im just going to keep redis_client usage for title since I didn't add it to interface yet to minimize change scope,
    # or I can quickly add it. Let's stick to the existing redis_client for title to avoid interface churn right now.
    
    title = redis_client.hget(f"conversation:{chat_id}:meta", "title")
    return {"id": chat_id, "title": title, "messages": messages}

@router.delete("/api/chats/{chat_id}")
async def delete_conversation_for_user(
    chat_id: str,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Attempting to delete chat_id: {chat_id} for user_id: {current_user.id}")
    owner_id = await crud_storage.get_conversation_owner(chat_id)
    if owner_id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if str(owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
    await crud_storage.delete_conversation(user_id=current_user.id, chat_id=chat_id)
    return {"ok": True, "detail": "Conversation deleted successfully"}

@router.get("/api/chats/latest", response_model=Dict)
async def get_latest_session(
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Fetching latest session ID for user_id: {current_user.id}")
    latest_id = await crud_storage.get_latest_conversation_id(user_id=current_user.id)
    return {"latest_session_id": latest_id}