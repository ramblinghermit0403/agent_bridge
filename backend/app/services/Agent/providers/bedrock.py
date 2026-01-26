import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_bedrock_llm(model_name: str = "apac.amazon.nova-pro-v1:0", region_name: Optional[str] = None, temperature: float = 0):
    """
    Creates and returns a ChatBedrock instance for AWS Bedrock models.
    
    Requires:
    - AWS credentials configured (via environment variables, ~/.aws/credentials, or IAM role)
    - AWS_DEFAULT_REGION or region_name parameter
    
    Args:
        model_name: The Bedrock model ID (e.g., 'apac.amazon.nova-pro-v1:0', 'anthropic.claude-3-sonnet-20240229-v1:0')
        region_name: AWS region. Defaults to AWS_DEFAULT_REGION env var.
        temperature: Model temperature for response randomness.
    """
    try:
        from langchain_aws import ChatBedrock
    except ImportError:
        logger.error("langchain-aws not installed. Run: pip install langchain-aws boto3")
        raise ImportError("langchain-aws is required for Bedrock support. Install with: pip install langchain-aws boto3")
    
    # Determine region
    final_region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    logger.info(f"Creating Bedrock LLM: model={model_name}, region={final_region}")
    
    # ChatBedrock uses boto3 under the hood, which automatically picks up credentials from:
    # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    # 2. ~/.aws/credentials file
    # 3. IAM role (if running on AWS infrastructure)
    
    return ChatBedrock(
        model_id=model_name,
        region_name=final_region,
        model_kwargs={
            "temperature": temperature,
        },
        streaming=True
    )
