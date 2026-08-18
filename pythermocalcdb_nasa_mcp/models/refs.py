from pydantic import BaseModel, Field


class MCPHTTPConfig(BaseModel):
    """
    Configuration for MCP HTTP transport.

    Attributes
    ----------
    host : str
        The HTTP bind host.
    port : int
        The HTTP bind port (1-65535).
    path : str
        The MCP HTTP endpoint path.
    """
    host: str = Field(
        default="127.0.0.1", description="HTTP bind host."
    )
    port: int = Field(
        default=8000, ge=1, le=65535, description="HTTP bind port."
    )
    path: str = Field(
        default="/mcp", description="MCP HTTP endpoint path."
    )
