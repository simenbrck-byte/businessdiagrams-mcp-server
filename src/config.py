from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )    

    APP_NAME: str = "github-batch-mcp-server"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"
    MCP_MOUNT_PATH: str = "/mcp"

    GITHUB_TOKEN: str = Field(..., description="GitHub token with contents read/write scope.")
    GITHUB_OWNER: str = Field(..., description="Owner or organization of the content repository.")
    GITHUB_REPO: str = Field(..., description="Repository name containing input/output folders.")
    GITHUB_BRANCH: str = Field("main", description="Branch to read from and write to.")

    MANIFEST_PATH: str = Field(
        "manifests/input_manifest.json",
        description="Ordered JSON manifest inside the content repo.",
    )
    OUTPUT_FOLDER: str = Field("output", description="Folder for per-file analysis output.")

    INDEX_BASE: int = Field(0, description="External index base accepted by tools. Set to 0 or 1.")

    COMMITTER_NAME: str | None = None
    COMMITTER_EMAIL: str | None = None

    REQUEST_TIMEOUT_SECONDS: float = 30.0
    MAX_IMAGE_BYTES: int = 20 * 1024 * 1024
    ALLOW_MARKDOWN_OUTPUT: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    if settings.INDEX_BASE not in (0, 1):
        raise ValueError("INDEX_BASE must be 0 or 1")
    return settings