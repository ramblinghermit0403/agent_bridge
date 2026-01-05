import json
from pydantic import create_model, Field, ConfigDict, BaseModel
from langchain_core.tools import StructuredTool
from typing import List, Dict, Any

class BedrockSafeModel(BaseModel):
    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        schema = super().model_json_schema(*args, **kwargs)
        
        def sanitize(obj):
            if isinstance(obj, dict):
                # Remove keys not supported by Bedrock/strict tools
                for key in ["title", "default"]:
                    if key in obj:
                        del obj[key]
                # Recurse
                for k, v in obj.items():
                    sanitize(v)
            elif isinstance(obj, list):
                for item in obj:
                    sanitize(item)
            return obj
            
        return sanitize(schema)

def debug_schema():
    fields = {
        "arg1": (str, Field(..., description="A required arg")),
        "arg2": (int, Field(5, description="An optional arg with default")),
        "arg3": (List[str], Field(default_factory=list, description="List arg"))
    }
    
    model_name = "TestToolInputModel"
    pydantic_model = create_model(
        model_name, 
        __config__=ConfigDict(title=None),
        __base__=BedrockSafeModel,
        **fields
    )
    
    def func(): pass
    
    tool = StructuredTool.from_function(
        func=func,
        name="test_tool_unique",
        description="A test tool",
        args_schema=pydantic_model
    )
    
    schema = tool.args_schema.model_json_schema()
    print(json.dumps(schema, indent=2))

if __name__ == "__main__":
    debug_schema()
