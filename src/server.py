from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="businessdiagrams-mcp-server")

@mcp.tool()
def ping() -> str:
    return "pong"

if __name__ == "__main__":
    import os

    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = int(os.environ.get("PORT", "8000"))

    mcp.run(transport="sse")