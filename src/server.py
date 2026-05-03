from mcp.server.fastmcp import FastMCP

from .config import get_settings

settings = get_settings()

mcp = FastMCP(
    settings.APP_NAME,
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
)

@mcp.tool()
def ping() -> str:
    return "pong"