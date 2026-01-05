import logging
from typing import Any, List, Optional, cast, Dict
import langchain_google_genai.chat_models
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

# Setup basic logging
logger = logging.getLogger(__name__)

# Conditionally import UsageMetadata
try:
    from langchain_core.messages import UsageMetadata
except ImportError:
    from typing import TypedDict
    class UsageMetadata(TypedDict, total=False):
        input_tokens: int
        output_tokens: int
        total_tokens: int
        input_token_details: Dict[str, Any]
        output_token_details: Dict[str, Any]

def apply_gemini_patch():
    """
    Applies the monkey patch for Gemini 2.5 Flash 'finish_reason' int crash.
    The installed version of langchain-google-genai expects finish_reason to be an enum with .name,
    but Gemini 2.5 Flash sometimes returns an int (e.g. 12).
    """
    
    # Conditionally import UsageMetadata and subtract_usage 
    # (relying on imports above, assuming standard langchain-core is available)
    
    try:
        from langchain_core.messages.ai import subtract_usage
    except ImportError:
        def subtract_usage(current: UsageMetadata, previous: UsageMetadata) -> UsageMetadata:
            return current

    try:
        _parse_response_candidate = langchain_google_genai.chat_models._parse_response_candidate
    except AttributeError:
        logger.warning("Could not find _parse_response_candidate, monkeypatch might fail.")
        def _parse_response_candidate(*args, **kwargs):
            return AIMessage(content="")

    def _patched_response_to_result(
        response: Any,
        stream: bool = False,
        prev_usage: Optional[UsageMetadata] = None,
    ) -> ChatResult:
        """Patched version of _response_to_result to handle int finish_reason."""
        llm_output = (
            {"prompt_feedback": response.prompt_feedback.model_dump()}
            if response.prompt_feedback
            else {}
        )

        # Get usage metadata
        lc_usage = None
        try:
            if response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count or 0
                thought_tokens = getattr(response.usage_metadata, "thoughts_token_count", 0) or 0
                
                candidates_tokens = response.usage_metadata.candidates_token_count or 0
                output_tokens = candidates_tokens + thought_tokens
                total_tokens = response.usage_metadata.total_token_count or 0
                
                cache_read_tokens = getattr(response.usage_metadata, "cached_content_token_count", 0) or 0
                
                if input_tokens + output_tokens + cache_read_tokens + total_tokens > 0:
                    cumulative_usage = UsageMetadata(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        input_token_details={"cache_read": cache_read_tokens} if cache_read_tokens else {},
                    )
                    
                    # previous usage metadata needs to be subtracted
                    lc_usage = subtract_usage(cumulative_usage, prev_usage) if prev_usage else cumulative_usage
        except Exception as e:
            lc_usage = None

        generations: List[ChatGeneration] = []

        for candidate in response.candidates or []:
            generation_info: dict[str, Any] = {}
            
            # --- FIX IS HERE ---
            if candidate.finish_reason:
                if hasattr(candidate.finish_reason, "name"):
                    generation_info["finish_reason"] = candidate.finish_reason.name
                else:
                    # Handle int or other types safely
                    generation_info["finish_reason"] = str(candidate.finish_reason)
            # -------------------

            generation_info["safety_ratings"] = (
                [safety_rating.model_dump() for safety_rating in candidate.safety_ratings]
                if candidate.safety_ratings
                else []
            )

            try:
                message = _parse_response_candidate(
                    candidate,
                    streaming=stream,
                    model_name=response.model_version if hasattr(response, "model_version") else None,
                    model_name_for_content=response.model_version if hasattr(response, "model_version") else None,
                )
            except TypeError:
                message = _parse_response_candidate(
                    candidate,
                    streaming=stream,
                )

            # Ensure response_metadata exists
            if not hasattr(message, "response_metadata"):
                message.response_metadata = {}
            
            # Add generation info to metadata
            message.response_metadata.update(generation_info)
            
            # Attach usage
            message.usage_metadata = lc_usage

            if stream:
                generations.append(
                    ChatGenerationChunk(
                        message=cast(AIMessageChunk, message),
                        generation_info=generation_info,
                    )
                )
            else:
                generations.append(
                    ChatGeneration(message=message, generation_info=generation_info)
                )

        if not response.candidates:
            if stream:
                generations = [
                    ChatGenerationChunk(
                        message=AIMessageChunk(content=""),
                        generation_info={},
                    )
                ]
            else:
                generations = [ChatGeneration(message=AIMessage(content=""), generation_info={})]

        return ChatResult(generations=generations, llm_output=llm_output)

    # Apply the patch
    langchain_google_genai.chat_models._response_to_result = _patched_response_to_result
    logger.info("Monkeypatched langchain_google_genai.chat_models._response_to_result for Gemini 2.5 compatibility.")
