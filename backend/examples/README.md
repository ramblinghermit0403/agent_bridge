# Example Scripts

This directory contains example scripts demonstrating how to interact with MCP servers and related infrastructure.

## Dynamic Client Registration

The `register_*.py` scripts demonstrate how to perform **Dynamic Client Registration** (RFC 7591) with supported MCP servers. This is an alternative to manually creating an application in the provider's developer dashboard.

### Usage

1.  Ensure you have `httpx` installed (`pip install httpx`).
2.  Run the script:
    ```bash
    python examples/register_figma_client.py
    ```
3.  If successful, the script will output a `Client ID` and `Client Secret`, which you should add to your `backend/.env` file.

**Note**: Not all MCP servers support dynamic registration. Check the specific server documentation.
