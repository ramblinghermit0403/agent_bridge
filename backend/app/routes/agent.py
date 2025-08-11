# import uuid
# import os
# import json
# import logging
# from typing import Optional, Any, AsyncGenerator # Added Optional, Any, AsyncGenerator
# from fastapi import status
# from fastapi import APIRouter, Depends, HTTPException, Request, Query # Added Query
# from pydantic import BaseModel, Field
# from sse_starlette.sse import EventSourceResponse
# from ..services.redis.redis_client import redis_client # Import the Redis client instance
# from ..database import database
# from sqlalchemy.ext.asyncio import AsyncSession
# # LangChain specific imports
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.agents import AgentExecutor # For type hinting
# from langchain_core.messages import SystemMessage, AIMessage
# from langchain_core.output_parsers import StrOutputParser
# from langchain_community.chat_message_histories import RedisChatMessageHistory
# # Project-specific imports from services and models
# from ..auth.oauth2 import get_current_user # Assuming you might use this later
# from ..models import User # Assuming you might use this later
# # Corrected path for get_session_memory and build_formatter_prompt
# from ..services.Agent.langchain_agent import get_session_memory, build_formatter_prompt, create_final_agent_pipeline

# # Setup basic logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # --- Pydantic Models for API Definition ---
# # Kept for clarity, though AskRequest isn't directly used for the GET /ask/stream body
# class AskRequest(BaseModel):
#     """Defines the structure of the incoming request body (for POST endpoints)."""
#     prompt: str
#     session_id: Optional[str] = Field(
#         None,
#         description="Unique ID for a specific conversation/tab. If not provided, a new one is generated."
#     )

# class AskResponse(BaseModel):
#     """Defines the structure of the response (for non-streaming endpoints)."""
#     output: str
#     user_id: str
#     session_id: str


# # --- Create the Router Instance ---
# router = APIRouter(tags=['Agent'])

# # --- Global Agent Executor Instance (Managed by Lifespan Events in main.py) ---
# # This will be populated by main.py's lifespan event.
# # It should not be None when get_agent_from_state is called.
# _global_agent_executor_instance: Optional[AgentExecutor] = None

# # --- Dependency Function to Access the Agent ---
# def get_agent_from_state(request: Request) -> AgentExecutor:
#     """
#     A dependency that retrieves the pre-loaded agent executor
#     from the main application's state.
#     """
#     # request.app.state.agent_executor_pipeline is where main.py stores it
#     agent_instance = request.app.state.agent_with_memory
#     if not agent_instance:
#         raise HTTPException(status_code=503, detail="Agent pipeline not initialized. Server starting up?")
#     return agent_instance


# # # --- SSE Streaming API Route ---


# from ..services.redis import crud_redis

# # --- Standard and FastAPI Imports ---
# import os
# import json
# import uuid
# import logging
# from typing import Optional, AsyncGenerator

# from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
# from sse_starlette.sse import EventSourceResponse
# from sqlalchemy.ext.asyncio import AsyncSession

# # --- LangChain Core Imports ---
# from langchain_core.messages import AIMessage
# from langchain_core.output_parsers import StrOutputParser
# # Old, incorrect import for your version

# # *** NEW: IMPORTS NEEDED FOR HANDLING TOOL OUTPUT ***
# from langchain_core.runnables.schema import StreamEvent
# from langchain_core.documents import Document
# # *** END NEW IMPORTS ***

# # --- LangChain Agent and LLM Imports ---
# from langchain.agents import AgentExecutor


# # --- Your Project's Local Imports ---

# # ... (Logger setup, router setup, etc.) ...

# #
# # The updated /ask/stream endpoint
# #
# @router.get("/ask/stream")
# async def ask_agent_stream(
#     fastapi_request: Request,
#     token: str = Query(...),
#     prompt: str = Query(..., min_length=1),
#     session_id: Optional[str] = Query(None),
#     agent_executor: AgentExecutor = Depends(get_agent_from_state),
#     db: AsyncSession = Depends(database.get_db),
# ) -> EventSourceResponse:
#     """
#     Handles a user's prompt, streams the output, and correctly manages conversation history in Redis.
#     """
#     current_user: User = await get_current_user(token, db)
#     if current_user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

#     actual_session_id = session_id or str(uuid.uuid4())
#     user_id = current_user.id
#     hybrid_session_key = f"{actual_session_id}"

#     # Check if this is a new conversation and create its metadata if so.
#     is_new_chat = not redis_client.exists(f"conversation:{actual_session_id}:meta")
    
#     if is_new_chat:
#         title = prompt[:35] + "..." if len(prompt) > 35 else prompt
#         crud_redis.create_new_conversation(
#             user_id=user_id,
#             chat_id=actual_session_id,
#             title=title
#         )

#     memory = get_session_memory(hybrid_session_key)
#     if memory is None:
#         raise HTTPException(status_code=503, detail="Conversation memory service is unavailable.")

#     # Manually add the user's message to the history BEFORE the stream
#     memory.add_user_message(prompt)

#     try:
#         chat_history = await memory.aget_messages()
#     except Exception as e:
#         logger.error(f"Failed to retrieve chat history for session {hybrid_session_key}: {e}", exc_info=True)
#         raise HTTPException(status_code=503, detail="Could not retrieve past conversation history.")
        
#     formatter_prompt = build_formatter_prompt()
#     llm_formatter = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)
#     formatter_chain = formatter_prompt | llm_formatter | StrOutputParser()

#     async def event_generator() -> AsyncGenerator[dict, None]:
#         plain_text_answer = ""
#         scratchpad_for_saving = []

#         try:
#             # Combine 'input' and 'chat_history' into a single dictionary
#             agent_input = {"input": prompt, "chat_history": chat_history}

#             # Call astream_events with the single, unified input dictionary
#             async for event in agent_executor.astream_events(agent_input, version="v1"):
#                 if await fastapi_request.is_disconnected():
#                     logger.warning(f"Client disconnected for session {hybrid_session_key}. Stopping stream.")
#                     break

#                 event_type = event["event"]
                
#                 if event_type == "on_tool_start":
#                     tool_name = event['name']
#                     tool_input = event['data']['input']
#                     thought = f"Tool Used: {tool_name} with input {json.dumps(tool_input)}"
#                     scratchpad_for_saving.append(thought)
#                     yield {"event": "scratchpad", "data": json.dumps({'type': 'tool_start', 'tool_name': tool_name, 'tool_input': tool_input})}
                
#                 elif event_type == "on_tool_end":
#                     tool_name = event['name']
#                     tool_output_obj = event['data']['output']
                    
#                     observation_text = ""
#                     # Use "duck typing" to safely unpack the tool result
#                     if hasattr(tool_output_obj, 'content') and isinstance(tool_output_obj.content, list):
#                         observation_text = "\n".join(
#                             [str(c.text) for c in tool_output_obj.content if hasattr(c, 'text')]
#                         )
#                     else:
#                         observation_text = str(tool_output_obj)

#                     thought = f"Tool Output: {observation_text}"
#                     scratchpad_for_saving.append(thought)
#                     yield {"event": "scratchpad", "data": json.dumps({'type': 'tool_end', 'tool_name': tool_name, 'observation': observation_text})}

#                 elif event_type == "on_llm_stream":
#                     if event['data']['chunk'].content:
#                         yield {"event": "llm_token", "data": json.dumps({'type': 'llm_token', 'content': event['data']['chunk'].content})}
                
#                 elif event_type == "on_chain_end" and event['name'] == 'AgentExecutor':
#                     output_data = event['data']['output']
#                     plain_text_answer = output_data.get('output', str(output_data)) if isinstance(output_data, dict) else str(output_data)

#                     html_answer = await formatter_chain.ainvoke({"question": prompt, "answer": plain_text_answer})
                    
#                     final_ai_message = AIMessage(
#                         content=plain_text_answer,
#                         additional_kwargs={ "scratchpad": scratchpad_for_saving, "html": html_answer }
#                     )
#                     memory.add_message(final_ai_message)

#                     yield {"event": "plain_text_answer", "data": json.dumps({'type': 'plain_text_answer', 'content': plain_text_answer})}
#                     yield {"event": "final_html_output", "data": json.dumps({'type': 'final_html_output', 'content': html_answer})}

#         except Exception as e:
#             logger.error(f"Error during SSE stream for session {hybrid_session_key}: {e}", exc_info=True)
#             yield {"event": "error", "data": json.dumps({'type': 'error', 'message': "An internal error occurred."})}
        
#         finally:
#             yield {"event": "stream_end", "data": json.dumps({'type': 'stream_end', 'session_id': actual_session_id, 'user_id': user_id})}
#             logger.info(f"Stream ended for session {hybrid_session_key}.")

#     return EventSourceResponse(event_generator(), media_type="text/event-stream")

# # In crud_redis.py

# def get_latest_conversation_id(user_id: int):
#     """Gets the ID of the most recent conversation for a user from Redis."""
#     user_conv_key = f"user:{user_id}:conversations"
#     # ZREVRANGE gets items from a sorted set, highest score (newest) first.
#     # (0, 0) means get only the first item (the most recent one).
#     latest_id_list = redis_client.zrevrange(user_conv_key, 0, 0)
#     return latest_id_list[0] if latest_id_list else None
# # In routers/chat.py

# from typing import Dict
# # ... your existing router setup ...

# from fastapi import APIRouter, Depends, HTTPException
# from typing import List, Dict
# import logging



# # # Setup logger and router
# # logger = logging.getLogger(__name__)


# @router.get("/api/chats/", response_model=List[Dict])
# def read_conversations_for_user(
#     current_user: User.User = Depends(get_current_user),
# ):
#     """
#     Retrieve a list of all conversations (ID and title) for the current user from Redis,
#     sorted with the newest first.
#     """
#     logger.info(f"Fetching conversation history for user_id: {current_user.id}")
#     return crud_redis.get_conversations_for_user(user_id=current_user.id)

# @router.get("/api/chats/{chat_id}")
# def read_conversation_messages(
#     chat_id: str,
#     current_user: User.User = Depends(get_current_user),
# ):
#     """
#     Retrieve all messages and metadata for a single conversation from Redis,
#     ensuring the user owns it.
#     """
#     logger.info(f"Fetching messages for chat_id: {chat_id} for user_id: {current_user.id}")
#     owner_id = crud_redis.get_conversation_owner(chat_id)

#     if owner_id is None:
#         raise HTTPException(status_code=404, detail="Conversation not found")
#     if owner_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
        
#     messages = crud_redis.get_conversation_details(chat_id)
#     title = crud_redis.redis_client.hget(f"conversation:{chat_id}:meta", "title")
    
#     return {"id": chat_id, "title": title, "messages": messages}

# @router.delete("/api/chats/{chat_id}")
# def delete_conversation_for_user(
#     chat_id: str,
#     current_user: User.User = Depends(get_current_user),
# ):
#     """
#     Delete a conversation and all its associated data from Redis.
#     """
#     logger.info(f"Attempting to delete chat_id: {chat_id} for user_id: {current_user.id}")
#     owner_id = crud_redis.get_conversation_owner(chat_id)

#     if owner_id is None:
#         raise HTTPException(status_code=404, detail="Conversation not found")
#     if owner_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
        
#     crud_redis.delete_conversation(user_id=current_user.id, chat_id=chat_id)
#     return {"ok": True, "detail": "Conversation deleted successfully"}



# @router.get("/api/chats/latest", response_model=Dict)
# def get_latest_session(
#     current_user: User.User = Depends(get_current_user),
# ):
#     """
#     Retrieve the session ID of the most recent conversation for the current user.
#     Returns `{"latest_session_id": "some-id"}` or `{"latest_session_id": null}`.
#     """
#     logger.info(f"Fetching latest session ID for user_id: {current_user.id}")
#     latest_id = crud_redis.get_latest_conversation_id(user_id=current_user.id)
#     return {"latest_session_id": latest_id}


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

# --- Your Project's Local Imports ---
from ..services.redis.redis_client import redis_client
from ..services.redis import crud_redis
from ..database import database
from ..auth.oauth2 import get_current_user
from ..models import User

# --- MODIFIED: Import the parameterized agent factory, not the global one ---
from ..services.Agent.langchain_agent import get_session_memory, build_formatter_prompt, create_final_agent_pipeline

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
    # REMOVED: No longer depends on a global agent state
    # agent_executor: AgentExecutor = Depends(get_agent_from_state),
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
    
    # 2. Create a new, user-specific agent executor for this single request.
    try:
        # This function must now be parameterized to accept user_servers
        agent_executor = await create_final_agent_pipeline(user_mcp_servers=user_servers)
    except Exception as e:
        logger.error(f"Failed to create agent pipeline for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not initialize the agent.")
    # --- END NEW ---

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
    llm_formatter = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)
    formatter_chain = formatter_prompt | llm_formatter | StrOutputParser()



    async def event_generator() -> AsyncGenerator[dict, None]:
        plain_text_answer = ""
        scratchpad_for_saving = []

        try:
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
                    tool_input = event['data']['input']
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