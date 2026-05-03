from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    settings.APP_NAME,
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
)

@mcp.tool()
def ping() -> str:
    return "pong"

if __name__ == "__main__":
    import os
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = int(os.environ.get("PORT", "8000"))
    mcp.run(transport="streamable-http")