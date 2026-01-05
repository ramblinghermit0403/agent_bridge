import logging
from functools import lru_cache
from typing import Optional

# Import separate providers
from .providers.gemini import get_gemini_llm

# Setup basic logging
logger = logging.getLogger(__name__)

@lru_cache(maxsize=16) 
def get_llm(model_provider: str = "gemini", model_name: str = "gemini-2.5-flash", region_name: Optional[str] = None):
    """
    Returns a cached instance of the LLM based on provider.
    Dispatches to specific provider modules.
    """
    
    # Normalize inputs
    if not model_provider:
        model_provider = "gemini"
        
    logger.info(f"--- LLM Factory Creating: {model_provider}/{model_name} ---")

    if model_provider == "gemini":
        return get_gemini_llm(model_name)
        
    else:
        # Fallback or extension point for other providers (OpenAI, Anthropic, etc.)
        # Bedrock support has been removed.
        raise ValueError(f"Unsupported model provider: {model_provider}")
