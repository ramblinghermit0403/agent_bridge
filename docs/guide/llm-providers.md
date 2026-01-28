# LLM Providers

The Agent Bridge supports multiple AI providers for language model intelligence.

## Supported Providers

### 1. Google Gemini (Default)
The primary reasoning engine, optimized for tool calling and agentic workflows.
*   **Env Var**: `GOOGLE_API_KEY`
*   **Default Model**: `gemini-2.5-flash`
*   **Available Models**:
    *   `gemini-2.5-flash` - Fast, cost-effective (Recommended).
    *   `gemini-2.5-pro` - Higher accuracy for complex reasoning.
    *   `gemini-1.5-pro` - Previous generation.

### 2. OpenAI
Full support for OpenAI's GPT models.
*   **Env Var**: `OPENAI_API_KEY`
*   **Default Model**: `gpt-4o`
*   **Available Models**:
    *   `gpt-4o` - Multimodal flagship model.
    *   `gpt-4-turbo` - Previous generation.
    *   `gpt-3.5-turbo` - Fastest, lowest cost.

### 3. AWS Bedrock (Disabled)
Currently disabled due to dependency conflicts with `langchain-aws`.
*   To enable, add `langchain-aws` to `pyproject.toml` and uncomment in `llm_factory.py`.

## How Provider Selection Works
The agent selects a provider based on the `model_provider` parameter passed during invocation.

**Code Path**: `server/app/services/agent/llm_factory.py`

```python
# The factory dispatches to provider-specific modules:
PROVIDER_MAP = {
    "gemini": get_gemini_llm,
    "openai": get_openai_llm,
    # "bedrock": get_bedrock_llm,  # Disabled
}
```

## Adding a New Provider
1.  Create a new file: `server/app/services/agent/providers/your_provider.py`.
2.  Implement a `get_your_provider_llm(model_name: str)` function.
3.  Register it in `PROVIDER_MAP` in `llm_factory.py`.

## Configuration
All providers are configured via environment variables in `server/.env`.

```bash
# Example .env configuration
GOOGLE_API_KEY="AIzaSy..."
OPENAI_API_KEY="sk-..."
```
