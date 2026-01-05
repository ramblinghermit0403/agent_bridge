import json
from pydantic import create_model, Field, ConfigDict, BaseModel
from typing import List, Dict, Any

# The proposed fix class
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

def test_fix():
    print("Testing create_model with __base__=BedrockSafeModel...")
    
    fields = {
        "arg1": (str, Field(..., description="A required arg")),
        "arg2": (int, Field(5, description="An optional arg with default")),
    }
    
    # Dynamic class to hold the config
    class ToolModel(BedrockSafeModel):
        model_config = ConfigDict(title=None)

    try:
        # Create the model using __base__
        model_name = "TestTool"
        pydantic_model = create_model(
            model_name,
            __base__=ToolModel,
            **fields
        )
        
        # Generate schema
        schema = pydantic_model.model_json_schema()
        print("Schema generated successfully.")
        print(json.dumps(schema, indent=2))
        
        # Validation checks
        schema_str = json.dumps(schema)
        if '"title":' in schema_str:
            print("FAIL: 'title' still found in schema!")
        elif '"default":' in schema_str:
            print("FAIL: 'default' still found in schema!")
        else:
            print("SUCCESS: Schema is clean!")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_fix()
