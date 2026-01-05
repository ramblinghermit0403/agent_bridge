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
        "Remember: Tools are your superpower. Use them!"
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

def build_formatter_prompt():
    """
    Builds a prompt for a presentation layer.
    """
    system_prompt = (
        "You are a frontend implementation expert. Your task is to format the answer as clean, semantic HTML "
        "to be rendered inside a chat bubble. \n"
        "RULES:\n"
        "1. DO NOT use <html>, <head>, <body>, or <!DOCTYPE> tags.\n"
        "2. DO NOT use inline `style` attributes. The frontend handles styling.\n"
        "3. Use only standard tags: <p>, <ul>, <ol>, <li>, <strong>, <em>, <table>, <thead>, <tbody>, <tr>, <th>, <td>.\n"
        "4. Start directly with the content (e.g., <p>Answer...</p>).\n"
        "5. For code blocks, use <pre><code>...</code></pre>.\n"
        "6. Do not add any new facts, strictly format the provided text."
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        ("user", "Question: {question}\nAnswer: {answer}\nFormat this answer as HTML:"),
    ]) 

def build_react_prompt():
    """
    Builds a ReAct-style prompt for models that don't support native tool calling well.
    """
    system_prompt = (
        "You are an expert assistant. Answer the following questions as best you can. "
        "You are designed to solving tasks using a specific Reason+Act (ReAct) process.\n\n"
        
        "You have access to the following tools:\n\n"
        "{tools}\n\n"
        
        "Use the following format strictly:\n\n"
        "Question: the input question you must answer\n"
        "Thought: you should always think about what to do\n"
        "Action: the action to take, should be one of [{tool_names}]\n"
        "Action Input: the input to the action (must be a valid string or JSON)\n"
        "Observation: the result of the action\n"
        "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
        "Thought: I now know the final answer\n"
        "Final Answer: the final answer to the original input question\n\n"
        
        "IMPORTANT RULES:\n"
        "1. You MUST use the exact headers: 'Thought:', 'Action:', 'Action Input:'. Do NOT bold them or change case.\n"
        "2. The 'Action' must be the EXACT name of a tool from the list.\n"
        "3. 'Action Input' MUST be a JSON object `{\"arg\": \"value\"}`. Do NOT send a plain string unless the tool takes exactly one argument.\n"
        "4. Output 'Observation:' ONLY if you are simulating a result (you usually wait for the system to provide it).\n"
        "5. If you receive an 'Invalid Format' observation, it means you forgot the 'Action:' or 'Action Input:' header. Retry immediately with correct formatting.\n"
        "6. Ensure there is a newline before 'Observation:'.\n\n"
        
        "EXAMPLE:\n"
        "Question: Check weather in SF\n"
        "Thought: I need to use check_weather.\n"
        "Action: check_weather\n"
        "Action Input: {\"location\": \"San Francisco\"}\n"
        "Observation: Sunny, 22C\n"
        "Thought: It is sunny.\n"
        "Final Answer: Sunny, 22C\n\n"
        
        "Begin!"
    )
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}\n\n{agent_scratchpad}"),
    ])
