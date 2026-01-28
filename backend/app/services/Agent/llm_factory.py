import logging
from functools import lru_cache
from typing import Optional, Callable

# Import separate providers
from .providers.gemini import get_gemini_llm
from .providers.openai import get_openai_llm
# from .providers.bedrock import get_bedrock_llm  # Disabled: requires langchain-aws which conflicts with current deps

# Setup basic logging
logger = logging.getLogger(__name__)

# Provider Registry
PROVIDER_MAP: dict[str, Callable] = {
    "gemini": get_gemini_llm,
    "openai": get_openai_llm,
    # "bedrock": get_bedrock_llm,  # Disabled: version conflict with langchain-core
    # Add new providers here:
    # "anthropic": get_anthropic_llm, 
}

@lru_cache(maxsize=16) 
def get_llm(model_provider: str = "gemini", model_name: str = "gemini-2.5-flash", region_name: Optional[str] = None):
    """
    Returns a cached instance of the LLM based on provider.
    Dispatches to specific provider modules via PROVIDER_MAP.
    """
    
    # Normalize inputs
    if not model_provider:
        model_provider = "gemini"
        
    logger.info(f"--- LLM Factory Creating: {model_provider}/{model_name} ---")

    provider_func = PROVIDER_MAP.get(model_provider.lower())
    
    if provider_func:
        return provider_func(model_name)
    else:
        supported = list(PROVIDER_MAP.keys())
        raise ValueError(f"Unsupported model provider: {model_provider}. Supported: {supported}")
