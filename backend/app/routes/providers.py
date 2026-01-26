"""
API routes for listing available LLM providers and models.
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["providers"])


class ModelConfig(BaseModel):
    """A single model configuration."""
    id: str  # Unique identifier for the model (e.g., "gemini-2.5-flash")
    name: str  # Human-readable name (e.g., "Gemini 2.5 Flash")
    provider: str  # Provider key (e.g., "gemini")


class ProviderConfig(BaseModel):
    """A single provider configuration."""
    id: str  # Unique identifier for the provider (e.g., "gemini")
    name: str  # Human-readable name (e.g., "Google Gemini")
    models: List[ModelConfig]


# Define available providers and models
# This is the single source of truth for the frontend.
# Future: could be loaded from a config file or database.
AVAILABLE_PROVIDERS: List[ProviderConfig] = [
    ProviderConfig(
        id="gemini",
        name="Google Gemini",
        models=[
            ModelConfig(id="gemini-2.5-flash", name="Gemini 2.5 Flash", provider="gemini"),
        ]
    ),
    ProviderConfig(
        id="openai",
        name="OpenAI",
        models=[
            ModelConfig(id="gpt-4o", name="GPT-4o", provider="openai"),
            ModelConfig(id="gpt-4o-mini", name="GPT-4o Mini", provider="openai"),
        ]
    ),
    # Bedrock disabled due to langchain-aws version conflict
    # ProviderConfig(
    #     id="bedrock",
    #     name="AWS Bedrock",
    #     models=[
    #         ModelConfig(id="apac.amazon.nova-pro-v1:0", name="Amazon Nova Pro", provider="bedrock"),
    #     ]
    # ),
]


@router.get("/providers", response_model=List[ProviderConfig])
async def get_available_providers():
    """
    Returns the list of available LLM providers and their models.
    The frontend uses this to populate model selection dropdowns.
    """
    return AVAILABLE_PROVIDERS
