import uuid
import os
import json
import logging
from typing import Optional, Any, AsyncGenerator, List, Dict # Added List, Dict

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
from ..services.redis.redis_client import redis_client
from ..services.redis import crud_redis
from ..database import database
from ..auth.oauth2 import get_current_user
from ..models import User
from ..services.tool_permissions_helper import check_tool_permission, check_tool_approval, PendingApproval
import asyncio

# --- MODIFIED: Import the parameterized agent factory, not the global one ---
# --- MODIFIED: Import the parameterized agent factory, not the global one ---
from ..services.Agent.langchain_agent import get_session_memory, build_formatter_prompt, get_llm
from ..services.agent_manager import get_or_create_agent
# --- NEW: Import for fetching user-specific data ---


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

# --- REMOVED: Global Agent and its Dependency Function ---
# _global_agent_executor_instance: Optional[AgentExecutor] = None
# def get_agent_from_state(request: Request) -> AgentExecutor: ...


# --- MODIFIED: The SSE Streaming API Route ---
@router.get("/ask/stream")
async def ask_agent_stream(
    fastapi_request: Request,
    token: str = Query(...),
    prompt: str = Query(..., min_length=1),
    session_id: Optional[str] = Query(None),
    model_provider: str = Query("gemini"), # new param
    model: str = Query("gemini-2.5-flash"), # new param, renamed from model_name for cleaner URL
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
    user_servers = await crud_redis.get_user_servers(db, user_id=current_user.id)
    
    # The rest of your code works as-is, now using the locally created `agent_executor`
    actual_session_id = session_id or str(uuid.uuid4())
    user_id = current_user.id
    hybrid_session_key = f"{actual_session_id}"

    is_new_chat = not redis_client.exists(f"conversation:{actual_session_id}:meta")
    if is_new_chat:
        title = prompt[:35] + "..." if len(prompt) > 35 else prompt
        crud_redis.create_new_conversation(user_id=user_id, chat_id=actual_session_id, title=title)

    memory = get_session_memory(hybrid_session_key)
    if memory is None:
        raise HTTPException(status_code=503, detail="Conversation memory service is unavailable.")

    memory.add_user_message(prompt)
    chat_history = await memory.aget_messages()
        
    formatter_prompt = build_formatter_prompt()
    # Note: Formatter should ideally reuse the same LLM or a lightweight one. 
    # Note: Formatter should reuse the same LLM to respect user choice and avoid quota issues.
    llm_formatter = get_llm(model_provider=model_provider, model_name=model)
    formatter_chain = formatter_prompt | llm_formatter | StrOutputParser()

    async def event_generator() -> AsyncGenerator[dict, None]:
        plain_text_answer = ""
        scratchpad_for_saving = []

        try:
            # 2. Get cached or create new agent
            try:
                # Notify user that we are checking/building agent
                start_msg = f"Initializing agent pipeline with {model}..."
                yield {"event": "scratchpad", "data": json.dumps({'type': 'agent_status', 'content': start_msg})}
                
                agent_executor, is_cache_hit = await get_or_create_agent(
                    user_id=current_user.id, 
                    user_servers=user_servers,
                    model_provider=model_provider,
                    model_name=model
                )
                
                if not is_cache_hit:
                     # It was a cold start, inform user it finished
                     yield {"event": "scratchpad", "data": json.dumps({'type': 'agent_status', 'content': "Agent initialized (Cold Start complete)."})}
            except Exception as e:
                 logger.error(f"Failed to create agent pipeline for user {current_user.id}: {e}", exc_info=True)
                 yield {"event": "error", "data": json.dumps({'type': 'error', 'message': "Could not initialize the agent."})}
                 return

            if not is_cache_hit:
                 yield {"event": "scratchpad", "data": json.dumps({'type': 'agent_status', 'content': "Agent initialized (Cold Start complete)."})}

            # Combine 'input' and 'chat_history' into a single dictionary
            agent_input = {"input": prompt, "chat_history": chat_history}

            # Call astream_events with the single, unified input dictionary
            async for event in agent_executor.astream_events(agent_input, version="v1"):
                if await fastapi_request.is_disconnected():
                    logger.warning(f"Client disconnected for session {hybrid_session_key}. Stopping stream.")
                    break

                event_type = event["event"]
                
                if event_type == "on_tool_start":
                    tool_name = event['name']
                    tool_input = event['data'].get("input", {})
                    
                    # Check if tool is enabled for this user
                    # Note: We'd need server_id here, which requires tracking which server the tool belongs to
                    # For now, we'll check approval only
                    
                    # Check if user has approval for this tool
                    needs_approval, approval_type = await check_tool_approval(db, user_id, tool_name)
                    
                    if needs_approval and approval_type != 'always':

                        # Create pending approval request (redundant if tool does it, but safer for UI consistency)
                        # Actually, if tool does it, we should just read it or let the tool created it.
                        # But tool creation is async inside the executor.
                        # The tool might have ALREADY created it or is about to.
                        # We can just send the signal. The tool blocks until approved.
                        
                        # We'll use a unique ID based on the tool call event to match if needed, 
                        # but check_tool_approval just checks DB.
                        
                        # Wait a tiny bit for the tool to create the pending record if it hasn't?
                        # Or we can create it here as well? 
                        # If we create it here, we need to ensure the tool uses the same ID or just checks for ANY pending.
                        # The tool logic we added checks PendingApproval.create() -> returns ID.
                        
                        # PROBLEM: We need the ID to send to frontend.
                        # But the tool generates the ID.
                        # We can't easily get the ID generated inside the tool unless we share state better.
                        
                        # WORKAROUND: We will assume the tool logic we added is authoritative.
                        # But we need to tell the frontend "Hey, approval required".
                        # And we need the approval_id.
                        
                        # The tool logic:
                        # approval_id = PendingApproval.create(...)
                        
                        # We can poll PendingApproval for an entry matching this user/tool/input?
                        # Or we can just create it here, and modify tool logic to use existing?
                        
                        # Modified strategy: Let agent.py create it (as it did before), 
                        # AND update the tool logic in langchain_agent.py to CHECK for existing pending instead of creating new?
                        
                        # Or simpler: The tool creates it. We poll for it here?
                        
                        # Let's poll for it.
                        approval_id = None
                        for _ in range(100): # Wait up to 10s for tool to register it
                           # Implementation detail: PendingApproval doesn't allow searching by content easily.
                           # But we can iterate _pending.
                           for pid, data in PendingApproval._pending.items():
                               if data['user_id'] == user_id and data['tool_name'] == tool_name and data['approved'] is None:
                                   approval_id = pid
                                   break
                           if approval_id: 
                               break
                           await asyncio.sleep(0.1)
                        
                        if approval_id:
                            yield {"event": "tool_approval_required", "data": json.dumps({
                                'type': 'tool_approval_required',
                                'approval_id': approval_id,
                                'tool_name': tool_name,
                                'server_name': 'unknown',
                                'payload': tool_input
                            })}
                        else:
                             # Fallback if tool didn't registers it (e.g. error or logic mismatch)
                             pass
                    
                    thought = f"Tool Used: {tool_name} with input {json.dumps(tool_input)}"
                    scratchpad_for_saving.append(thought)
                    yield {"event": "scratchpad", "data": json.dumps({'type': 'tool_start', 'tool_name': tool_name, 'tool_input': tool_input})}
                
                elif event_type == "on_tool_end":
                    tool_name = event['name']
                    tool_output_obj = event['data']['output']
                    
                    observation_text = ""
                    # Use "duck typing" to safely unpack the tool result
                    if hasattr(tool_output_obj, 'content') and isinstance(tool_output_obj.content, list):
                        observation_text = "\n".join(
                            [str(c.text) for c in tool_output_obj.content if hasattr(c, 'text')]
                        )
                    else:
                        observation_text = str(tool_output_obj)

                    thought = f"Tool Output: {observation_text}"
                    scratchpad_for_saving.append(thought)
                    yield {"event": "scratchpad", "data": json.dumps({'type': 'tool_end', 'tool_name': tool_name, 'observation': observation_text})}

                elif event_type == "on_llm_stream":
                    if event['data']['chunk'].content:
                        yield {"event": "llm_token", "data": json.dumps({'type': 'llm_token', 'content': event['data']['chunk'].content})}
                
                elif event_type == "on_chain_end" and event['name'] == 'AgentExecutor':
                    output_data = event['data']['output']
                    plain_text_answer = output_data.get('output', str(output_data)) if isinstance(output_data, dict) else str(output_data)

                    html_answer = await formatter_chain.ainvoke({"question": prompt, "answer": plain_text_answer})
                    
                    final_ai_message = AIMessage(
                        content=plain_text_answer,
                        additional_kwargs={ "scratchpad": scratchpad_for_saving, "html": html_answer }
                    )
                    memory.add_message(final_ai_message)

                    yield {"event": "plain_text_answer", "data": json.dumps({'type': 'plain_text_answer', 'content': plain_text_answer})}
                    yield {"event": "final_html_output", "data": json.dumps({'type': 'final_html_output', 'content': html_answer})}

        except ResourceExhausted:
            logger.warning(f"Gemini quota exceeded for session {hybrid_session_key}.")
            yield {"event": "error", "data": json.dumps({'type': 'error', 'message': "My brain is tired (Gemini Quota Exceeded). Please give me a moment to rest and try again."})}

        except ServiceUnavailable as e:
            logger.warning(f"Gemini service unavailable for session {hybrid_session_key}: {e}")
            yield {"event": "error", "data": json.dumps({'type': 'error', 'message': "The AI service is momentarily unavailable. Please try again shortly."})}

        except Exception as e:
            logger.error(f"Error during SSE stream for session {hybrid_session_key}: {e}", exc_info=True)
            yield {"event": "error", "data": json.dumps({'type': 'error', 'message': "An internal error occurred."})}
        
        finally:
            yield {"event": "stream_end", "data": json.dumps({'type': 'stream_end', 'session_id': actual_session_id, 'user_id': user_id})}
            logger.info(f"Stream ended for session {hybrid_session_key}.")

    return EventSourceResponse(event_generator(), media_type="text/event-stream")



# --- UNCHANGED: Your other routes for managing chat history are fine ---

@router.get("/api/chats/", response_model=List[Dict])
def read_conversations_for_user(
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Fetching conversation history for user_id: {current_user.id}")
    return crud_redis.get_conversations_for_user(user_id=current_user.id)

@router.get("/api/chats/{chat_id}")
def read_conversation_messages(
    chat_id: str,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Fetching messages for chat_id: {chat_id} for user_id: {current_user.id}")
    owner_id = crud_redis.get_conversation_owner(chat_id)
    if owner_id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
    messages = crud_redis.get_conversation_details(chat_id)
    title = crud_redis.redis_client.hget(f"conversation:{chat_id}:meta", "title")
    return {"id": chat_id, "title": title, "messages": messages}

@router.delete("/api/chats/{chat_id}")
def delete_conversation_for_user(
    chat_id: str,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Attempting to delete chat_id: {chat_id} for user_id: {current_user.id}")
    owner_id = crud_redis.get_conversation_owner(chat_id)
    if owner_id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
    crud_redis.delete_conversation(user_id=current_user.id, chat_id=chat_id)
    return {"ok": True, "detail": "Conversation deleted successfully"}

@router.get("/api/chats/latest", response_model=Dict)
def get_latest_session(
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Fetching latest session ID for user_id: {current_user.id}")
    latest_id = crud_redis.get_latest_conversation_id(user_id=current_user.id)
    return {"latest_session_id": latest_id}