import json
import logging
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from langchain_core.messages import AIMessage
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from ..services.security.permissions import PendingApproval
from ..services.agent.agent_factory import get_session_memory

logger = logging.getLogger(__name__)

async def stream_agent_events(
    agent_executor, 
    agent_input: Dict[str, Any], 
    config: Dict[str, Any], 
    session_id: str, 
    user_id: str,
    resume: bool = False
) -> AsyncGenerator[dict, None]:
    """
    Generator that executes the agent and yields SSE-compatible events.
    Handles error catching, polling for pending approvals, and response formatting.
    """
    
    hybrid_session_key = session_id
    plain_text_answer = ""
    scratchpad_for_saving = []
    
    # Capture start time to filter out old/stale pending approvals
    stream_start_time = datetime.utcnow()
    
    # Get memory instance for saving final answer
    memory = get_session_memory(hybrid_session_key)

    try:
        logger.info(f"Starting stream for session {session_id} (resume={resume})")
        
        async for event in agent_executor.astream_events(agent_input, config=config, version="v1"):
            event_type = event["event"]
            
            if event_type == "on_tool_start":
                tool_name = event['name']
                tool_input = event['data'].get("input", {})
                
                # Polling logic for PendingApproval (Legacy / Fallback)
                # Note: Graph interrupt usually handles this, but we keep this for robust feedback
                approval_id = None
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

            elif event_type == "on_chat_model_stream":
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
                # Logic to determine if this is the FINAL output
                event_name = event.get('name', '')
                output_data = event['data'].get('output')
                
                is_final_output = False
                
                if event_name == 'AgentExecutor':
                    is_final_output = True
                elif output_data and isinstance(output_data, dict) and 'messages' in output_data:
                    messages = output_data['messages']
                    # Check if last message is AI and NOT a tool call
                    if messages and hasattr(messages[-1], 'type'):
                        is_final_output = messages[-1].type == 'ai' and not hasattr(messages[-1], 'tool_calls') or (hasattr(messages[-1], 'tool_calls') and not messages[-1].tool_calls)
                
                if is_final_output and output_data and isinstance(output_data, dict):
                    # Extract plain text
                    if isinstance(output_data, dict) and 'output' in output_data:
                        plain_text_answer = output_data['output']
                    elif isinstance(output_data, dict) and 'messages' in output_data:
                        messages = output_data['messages']
                        if messages and hasattr(messages[-1], 'content'):
                            content = messages[-1].content
                            if isinstance(content, list):
                                plain_text_answer = " ".join(
                                    str(block.get('text', block)) if isinstance(block, dict) else str(block)
                                    for block in content
                                )
                            else:
                                plain_text_answer = str(content)
                    
                    # Only process if valid
                    if plain_text_answer and isinstance(plain_text_answer, str) and plain_text_answer.strip():
                        # Save final answer to memory
                        if memory:
                            final_ai_message = AIMessage(
                                content=plain_text_answer,
                                additional_kwargs={ "scratchpad": scratchpad_for_saving }
                            )
                            memory.add_message(final_ai_message)

                        yield {"event": "plain_text_answer", "data": json.dumps({'type': 'plain_text_answer', 'content': plain_text_answer})}

        # CRITICAL FIX: Check for pending approvals that caused a graph interrupt
        pending_snapshot = list(PendingApproval._pending.items())
        for pid, data in pending_snapshot:
            if data['user_id'] == user_id and data['approved'] is None:
                 created_at = data.get('created_at')
                 if not resume and created_at and created_at < stream_start_time:
                     continue
                 
                 # Small delay to ensure previous events are flushed
                 await asyncio.sleep(0.0) 

                 yield {"event": "tool_approval_required", "data": json.dumps({
                    'type': 'tool_approval_required',
                    'approval_id': pid,
                    'tool_name': data.get('tool_name'),
                    'server_name': data.get('server_name', 'unknown'),
                    'payload': data.get('tool_input', {})
                 })}
                 
                 await asyncio.sleep(0.1)

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
        yield {"event": "stream_end", "data": json.dumps({'type': 'stream_end', 'session_id': session_id, 'user_id': user_id})}
        logger.info(f"Stream ended for session {hybrid_session_key}.")
