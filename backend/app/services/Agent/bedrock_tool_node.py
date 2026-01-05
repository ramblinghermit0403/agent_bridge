import logging
from typing import Any, Dict, List
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)

class BedrockToolNode:
    """
    Custom tool execution node for Bedrock models.
    
    Bedrock's Converse API is strict about tool message formatting:
    - Tool call IDs must match exactly
    - ToolMessage objects must have minimal metadata
    - No extra fields that aren't explicitly supported
    
    This node ensures compatibility by:
    1. Extracting tool calls from the last AIMessage
    2. Executing tools using their async invoke methods
    3. Creating clean ToolMessage objects with only required fields
    """
    
    def __init__(self, tools):
        self.tools_by_name = {tool.name: tool for tool in tools}
        logger.info(f"BedrockToolNode initialized with {len(tools)} tools")
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, List]:
        """
        Execute tools and return ToolMessage objects.
        
        Args:
            state: AgentState dict containing 'messages' list
            
        Returns:
            Dict with 'messages' key containing list of ToolMessage objects
        """
        messages = state.get("messages", [])
        if not messages:
            logger.warning("BedrockToolNode: No messages in state")
            return {"messages": []}
        
        last_message = messages[-1]
        
        # Extract tool calls from the AIMessage
        tool_calls = getattr(last_message, "tool_calls", [])
        if not tool_calls:
            logger.warning("BedrockToolNode: No tool_calls in last message")
            return {"messages": []}
        
        logger.info(f"BedrockToolNode: Executing {len(tool_calls)} tool(s)")
        
        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            tool_id = tool_call["id"]
            
            logger.info(f"BedrockToolNode: Executing {tool_name} with ID {tool_id}")
            
            # Get the tool
            if tool_name not in self.tools_by_name:
                error_msg = f"Tool '{tool_name}' not found"
                logger.error(f"BedrockToolNode: {error_msg}")
                tool_msg = ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name
                )
                tool_messages.append(tool_msg)
                continue
            
            tool = self.tools_by_name[tool_name]
            
            # Execute the tool
            try:
                result = await tool.ainvoke(tool_args)
                result_str = str(result)
                logger.info(f"BedrockToolNode: {tool_name} succeeded ({len(result_str)} chars)")
            except Exception as e:
                result_str = f"Error executing tool: {str(e)}"
                logger.error(f"BedrockToolNode: {tool_name} failed: {e}", exc_info=True)
            
            # Create minimal ToolMessage (Bedrock-safe)
            # Only include required fields: content, tool_call_id, name
            tool_msg = ToolMessage(
                content=result_str,
                tool_call_id=tool_id,  # Exact ID match is critical
                name=tool_name
            )
            tool_messages.append(tool_msg)
        
        logger.info(f"BedrockToolNode: Returning {len(tool_messages)} tool message(s)")
        return {"messages": tool_messages}
