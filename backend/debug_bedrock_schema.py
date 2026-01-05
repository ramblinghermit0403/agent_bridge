import json
from pydantic import create_model, Field, ConfigDict
from langchain_core.tools import StructuredTool

def debug_schema():
    # Mimic the logic in tools.py
    tool_name = "test-tool"
    description = "A test tool"
    
    # Mimic an MCP schema with default values (which Pydantic might include in JSON schema)
    # Bedrock sometimes hates 'default' in the schema if not carefully handled
    fields = {
        "arg1": (str, Field(..., description="A required arg")),
        "arg2": (int, Field(5, description="An optional arg with default")),
    }
    
    model_name = "TestToolInputModel"
    pydantic_model = create_model(
        model_name, 
        __config__=ConfigDict(title=None),
        **fields
    )
    
    def func(): pass
    
    tool = StructuredTool.from_function(
        func=func,
        name="test_tool_unique",
        description=description,
        args_schema=pydantic_model
    )
    
    # Get the definition that LangChain would send (approximate)
    # The ChatBedrockConverse model converts this tool to Bedrock's format.
    # We can inspect tool.args_schema.model_json_schema()
    
    schema = tool.args_schema.model_json_schema()
    print(json.dumps(schema, indent=2))

if __name__ == "__main__":
    debug_schema()
