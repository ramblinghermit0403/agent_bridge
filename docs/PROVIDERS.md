# Supported Providers

The Agent Bridge supports various AI providers for LLM intelligence and Vector Search.

## Logic / LLM Providers

### 1. Google Gemini (Primary)
The default reasoning engine.
- **Env Var**: `GOOGLE_API_KEY`
- **Models**: `gemini-1.5-pro` (Reasoning), `gemini-1.5-flash` (Speed)

### 2. AWS Bedrock (Optional)
Supported via LangChain integration.
- **Env Vars**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- **Models**: Claude 3 (Haiku/Sonnet/Opus)

## Vector Database Providers

### 1. Pinecone
Used for Long-term Memory (RAG).
- **Env Vars**: 
    - `PINECONE_API_KEY`
    - `PINECONE_ENVIRONMENT`
    - `PINECONE_INDEX_NAME`

## Configuration
All providers are configured in `backend/.env`.

```bash
# Example .env configuration
GOOGLE_API_KEY="AIzaSy..."
PINECONE_API_KEY="pc-..."
```
