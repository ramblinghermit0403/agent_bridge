from langchain_openai import ChatOpenAI
import os

def get_openai_llm(model_name: str = "gpt-4o"):
    """
    Returns an OpenAI Chat Model.
    Ensure OPENAI_API_KEY is set in your environment.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
        
    return ChatOpenAI(
        model=model_name,
        temperature=0,
        streaming=True,
        api_key=api_key
    )
