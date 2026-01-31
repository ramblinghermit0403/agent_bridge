from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

def build_agent_prompt(model_provider: str = "gemini"):
    """
    Builds a prompt for an agent that knows how to use
    both specific tools and a general knowledge base.
    """
    # Universal system prompt for all models
    system_prompt = (
        "You are an expert assistant. Your goal is to answer a user's question accurately and concisely.\n"
        "You have access to a set of specialized tools for specific, structured tasks (like checking a server status).\n"
        "You ALSO have access to a general knowledge base via the `search_knowledge_base` tool.\n\n"
        "Follow these rules for choosing a tool:\n"
        "1. First, check if the user's question can be directly answered by one of the specialized tools. If it's a clear match, use that tool.\n"
        # "2. If the question is more general, open-ended, or asks about policies, conventions, or information not covered by the specialized tools, you MUST use the `search_knowledge_base` tool.\n"
        
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

def build_langgraph_prompt():
    """
    Builds a prompt compatible with LangGraph state (list of messages).
    """
    # Stronger prompt to encourage tool usage (especially for Bedrock)
    system_prompt = (
        "You are an expert assistant with access to specialized tools. "
        "Your primary job is to USE TOOLS to accomplish tasks.\n\n"
        "CRITICAL RULES:\n"
        "1. If the user asks you to search, fetch, create, update, or interact with external systems (GitHub, Notion, databases, etc.), you MUST use the appropriate tool.\n"
        "2. Do NOT attempt to answer from memory if a tool can provide current, accurate information.\n"
        "3. When you identify a relevant tool, call it immediately.\n"
        "4. After receiving tool results, synthesize them into a clear, concise answer.\n\n"
        "RESPONSE STYLE:\n"
        "- Format your output using **Markdown** to make it structurally beautiful and easy to read.\n"
        "- Use `### Headers` to separate logical sections.\n"
        "- Use **Bold** for key terms, numbers, or statuses.\n"
        "- Use `Lists` or `- Bullet points` for steps or multiple items.\n"
        "- Use `Tables` if you are presenting structured data (like a list of issues or PRs).\n"
        "- Be concise. Do not use filler phrases like 'Here is the information you requested'. Just give the answer.\n\n"
        "PERMISSION HANDLING:\n"
        "- If a tool returns an error saying 'User denied permission', acknowledge it for THAT request only.\n"
        "- When the user sends a NEW message asking for the same action, you MUST use the tool again.\n"
        "- Permission denials do NOT persist across different user messages. Always retry on new requests.\n\n"
        "Remember: Tools are your superpower. Use them!"
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

# Formatter and ReAct prompts removed as they are unused.
