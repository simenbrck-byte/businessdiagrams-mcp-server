from __future__ import annotations

import contextlib

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import get_settings
from .server import mcp

settings = get_settings()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "mcp_url": "/mcp",
    }


@app.get("/debug/tools")
async def debug_tools():
    tools = mcp._tool_manager._tools
    return {
        "count": len(tools),
        "tools": list(tools.keys()),
    }


app.mount(
    "/mcp",
    mcp.streamable_http_app(),
)