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
from ..services.redis.redis_client import redis_client
from ..services.redis import crud_redis
from ..database import database
from ..auth.oauth2 import get_current_user
from ..models import User
from ..services.tool_permissions_helper import check_tool_permission, check_tool_approval, PendingApproval
import asyncio

# --- MODIFIED: Import the parameterized agent factory, not the global one ---
# --- MODIFIED: Import the parameterized agent factory, not the global one ---
from ..services.Agent.langchain_agent import get_session_memory, get_llm
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

    # Get history BEFORE adding the new message to avoid duplication in the prompt
    chat_history = await memory.aget_messages()

    # Only add message if NOT resuming
    if not resume:
        memory.add_user_message(prompt)
        
    # Formatter removed for client-side markdown rendering optimization
    # formatter_prompt = build_formatter_prompt()
    # llm_formatter = get_llm(model_provider=model_provider, model_name=model)
    # formatter_chain = formatter_prompt | llm_formatter | StrOutputParser()

    async def event_generator() -> AsyncGenerator[dict, None]:
        plain_text_answer = ""
        scratchpad_for_saving = []

        try:
            # 2. Get cached or create new agent
            try:
                # Notify user that we are checking/building agent
                start_msg = f"Initializing agent pipeline with {model}..."
                if resume:
                    start_msg = f"Resuming agent execution..."
                
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
            if resume:
                # Resume: empty input relies on preserved graph state
                # We do NOT pass chat_history again to avoid duplication if graph persists it.
                # However, our GraphAgentExecutor manual invoke logic might want history?
                # Actually, if we pass empty input, GraphAgentExecutor sees no "input" key.
                # But it might add chat_history if present. 
                # For resume, we want pure state resumption.
                agent_input = {} 
            else:
                agent_input = {"input": prompt, "chat_history": chat_history}

            # Call astream_events with the single, unified input dictionary
            # Pass user_id in config for permission checking in route_tools
            # Pass thread_id for LangGraph state persistence per session
            config = {"configurable": {"user_id": user_id, "thread_id": actual_session_id}}
            
            logger.info(f"Starting stream for session {actual_session_id} (resume={resume})")
            
            # Capture start time to filter out old/stale pending approvals
            stream_start_time = datetime.utcnow()

            async for event in agent_executor.astream_events(agent_input, config=config, version="v1"):
                if await fastapi_request.is_disconnected():
                    logger.warning(f"Client disconnected for session {hybrid_session_key}. Stopping stream.")
                    break

                event_type = event["event"]
                # DEBUG LOG: See exactly what LangGraph is emitting
                # logger.info(f"Event: {event_type} | Name: {event.get('name')} | Keys: {event.get('data', {}).keys()}")
                
                if event_type == "on_tool_start":
                    tool_name = event['name']
                    tool_input = event['data'].get("input", {})
                    
                    # Check if tool is enabled for this user
                    # (Note: we already checked permissions in graph_agent, but double check doesn't hurt)
                    if user_servers:
                        # Logic to check enablement if needed, but we rely on graph blocking now
                        pass

                    # Polling logic for PendingApproval (Legacy / Fallback)
                    # We still keep this if the tool managed to start but is somehow blocked continuously
                    # But graph interrupt handles this differently.
                    approval_id = None
                    # Short poll just in case
                    for _ in range(5): 
                       for pid, data in PendingApproval._pending.items():
                           if data['user_id'] == user_id and data['tool_name'] == tool_name and data['approved'] is None:
                               # Check timestamp
                               created_at = data.get('created_at')
                               if created_at and created_at < stream_start_time:
                                   continue
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

                    thought = f"Tool Used: {tool_name} with input {json.dumps(tool_input)}"
                    scratchpad_for_saving.append(thought)
                    yield {"event": "scratchpad", "data": json.dumps({'type': 'tool_start', 'tool_name': tool_name, 'tool_input': tool_input})}

                if event_type == "on_chat_model_stream":
                    # Stream actual tokens
                    content = event['data']['chunk'].content
                    if content:
                         yield {"event": "llm_token", "data": json.dumps({'type': 'llm_token', 'content': content})}



                
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
                
                elif event_type == "on_chain_end":
                    event_name = event.get('name', '')
                    output_data = event['data'].get('output')
                    
                    # Handle both AgentExecutor (legacy) and LangGraph events
                    # AgentExecutor emits with name 'AgentExecutor' and output dict with 'output' key
                    # LangGraph emits with output dict containing 'messages' list
                    # IMPORTANT: Only process the FINAL chain_end, not intermediate tool/node completions
                    is_final_output = False
                    
                    if event_name == 'AgentExecutor':
                        is_final_output = True
                    elif output_data and isinstance(output_data, dict) and 'messages' in output_data:
                        # For LangGraph: only process if this is the final graph output
                        # (not intermediate node outputs like tool execution)
                        messages = output_data['messages']
                        # Final output has the complete conversation including tool results and final AI response
                        # Check if last message is an AIMessage (not ToolMessage)
                        if messages and hasattr(messages[-1], 'type'):
                            is_final_output = messages[-1].type == 'ai' and not hasattr(messages[-1], 'tool_calls') or (hasattr(messages[-1], 'tool_calls') and not messages[-1].tool_calls)
                    
                    if is_final_output and output_data and isinstance(output_data, dict):
                        # Extract plain text from different formats
                        if isinstance(output_data, dict) and 'output' in output_data:
                            plain_text_answer = output_data['output']
                        elif isinstance(output_data, dict) and 'messages' in output_data:
                            # LangGraph format
                            messages = output_data['messages']
                            if messages and hasattr(messages[-1], 'content'):
                                content = messages[-1].content
                                # Content can be a string or a list (multi-modal)
                                if isinstance(content, list):
                                    # Extract text from list of content blocks
                                    plain_text_answer = " ".join(
                                        str(block.get('text', block)) if isinstance(block, dict) else str(block)
                                        for block in content
                                    )
                                else:
                                    plain_text_answer = str(content)
                            else:
                                continue
                        else:
                            continue
                        
                        # Only process if we have content
                        if plain_text_answer and isinstance(plain_text_answer, str) and plain_text_answer.strip():
                            # Save final answer to memory (no HTML)
                            final_ai_message = AIMessage(
                                content=plain_text_answer,
                                additional_kwargs={ "scratchpad": scratchpad_for_saving }
                            )
                            memory.add_message(final_ai_message)

                            yield {"event": "plain_text_answer", "data": json.dumps({'type': 'plain_text_answer', 'content': plain_text_answer})}

            # CRITICAL FIX: Check for pending approvals that caused a graph interrupt
            # The graph stops *before* tool execution, so on_tool_start never fires.
            # We must manually check if a pending approval exists for this user.
            # CRITICAL FIX: Check for pending approvals that caused a graph interrupt
            # The graph stops *before* tool execution, so on_tool_start never fires.
            # We must manually check if a pending approval exists for this user.
            pending_snapshot = list(PendingApproval._pending.items())
            for pid, data in pending_snapshot:
                if data['user_id'] == user_id and data['approved'] is None:
                     # Check timestamp if available (legacy records might not have it)
                     # CRITICAL: If we are RESUMING, we expect an existing approval, so ignore timestamp check.
                     created_at = data.get('created_at')
                     if not resume and created_at and created_at < stream_start_time:
                         logger.info(f"Skipping stale pending approval {pid} created at {created_at}")
                         continue
                     logger.info(f"Found pending approval {pid} for user {user_id} after stream end.")
                     
                     # Small delay to ensure previous events are flushed before this critical one
                     await asyncio.sleep(0.0) 

                     yield {"event": "tool_approval_required", "data": json.dumps({
                        'type': 'tool_approval_required',
                        'approval_id': pid,
                        'tool_name': data.get('tool_name'),
                        'server_name': data.get('server_name', 'unknown'),
                        'payload': data.get('tool_input', {})
                     })}
                     
                     # Only emit one to avoid confusing the frontend
                     # Wait a tiny bit to ensure the client receives this before we close the stream
                     await asyncio.sleep(0.1)
                     break

        except ResourceExhausted:
            logger.warning(f"Gemini quota exceeded for session {hybrid_session_key}.")
            yield {"event": "server_error", "data": json.dumps({'type': 'error', 'message': "My brain is tired (Gemini Quota Exceeded). Please give me a moment to rest and try again."})}

        except ServiceUnavailable as e:
            logger.warning(f"Gemini service unavailable for session {hybrid_session_key}: {e}")
            yield {"event": "server_error", "data": json.dumps({'type': 'error', 'message': "The AI service is momentarily unavailable. Please try again shortly."})}

        except Exception as e:
            logger.error(f"Error during SSE stream for session {hybrid_session_key}: {e}", exc_info=True)
            yield {"event": "server_error", "data": json.dumps({'type': 'error', 'message': "An internal error occurred."})}
        
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