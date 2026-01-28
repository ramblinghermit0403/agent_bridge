class RequiresAuthenticationError(Exception):
    """
    Raised when an MCP server requires re-authentication (token refresh failed and no fallback available).
    This signal should be caught by the API layer to return a 401 response.
    """
    def __init__(self, server_name: str, message: str = "Authentication required"):
        self.server_name = server_name
        self.message = message
        super().__init__(f"{message} for {server_name}")
