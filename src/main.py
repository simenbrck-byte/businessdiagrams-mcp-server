from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import get_settings
from .server import mcp

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "mcp_path": settings.MCP_MOUNT_PATH,
            "status": "ok",
        }
    )

@app.get("/healthz", include_in_schema=False)
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})

mcp_app = mcp.streamable_http_app(streamable_http_path="/")
app.mount(
    settings.MCP_MOUNT_PATH,
    mcp.streamable_http_app(),
)