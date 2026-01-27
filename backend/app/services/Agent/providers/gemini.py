import os
import logging

logger = logging.getLogger(__name__)

def get_gemini_llm(model_name: str = "gemini-2.5-flash", temperature: float = 0):
    """
    Creates and returns a ChatGoogleGenerativeAI instance.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        logger.error("langchain_google_genai not installed.")
        raise

    """
    Creates and returns a ChatGoogleGenerativeAI instance.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"DEBUG: Using Gemini API Key: {api_key}", flush=True) # Debug print
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found in environment")
        
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature
    )
