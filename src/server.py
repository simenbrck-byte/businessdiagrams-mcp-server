from __future__ import annotations

import json
from typing import Any, Literal

from mcp.server.mcpserver import Image, MCPServer

from .config import get_settings
from .github_api import GithubRepoClient
from .manifest_service import ManifestService
from .models import SavedAnalysisEnvelope

settings = get_settings()
github_client = GithubRepoClient(settings)
manifest_service = ManifestService(github_client, settings.MANIFEST_PATH)

mcp = MCPServer(settings.APP_NAME)

def _png_bytes_to_mcp_image(data: bytes) -> Image:
    if len(data) > settings.MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image exceeds MAX_IMAGE_BYTES ({settings.MAX_IMAGE_BYTES} bytes)."
        )
    return Image(data=data, format="png")


@mcp.tool()
async def get_total_files() -> int:
    """Return the total number of files in the configured GitHub manifest."""
    return await manifest_service.total_files()

@mcp.tool()
async def get_file_by_index(index: int) -> Image:
    """Return exactly one PNG image from the manifest as an MCP Image."""
    _, entry = await manifest_service.entry_for_external_index(index, settings.INDEX_BASE)
    gh_file = await github_client.read_binary_file(entry.path)
    return _png_bytes_to_mcp_image(gh_file.content_bytes)


@mcp.tool()
async def save_analysis_result(
    index: int,
    analysis: dict[str, Any],
    output_format: Literal["json", "markdown"] = "json",
) -> dict[str, Any]:
    """Save the worker agent's analysis result for one manifest entry to GitHub."""
    internal_index, entry = await manifest_service.entry_for_external_index(index, settings.INDEX_BASE)

    stem = entry.file_name.rsplit(".", 1)[0]
    extension = "json" if output_format == "json" else "md"
    output_path = f"{settings.OUTPUT_FOLDER}/{stem}.{extension}"

    envelope = SavedAnalysisEnvelope(
        seq=entry.seq,
        index=internal_index,
        index_base=settings.INDEX_BASE,
        input_file=entry.file_name,
        input_path=entry.path,
        content_repo=f"{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}",
        content_branch=settings.GITHUB_BRANCH,
        output_format=output_format,
        analysis=analysis,
    )

    if output_format == "json":
        rendered = json.dumps(envelope.model_dump(), ensure_ascii=False, indent=2)
    else:
        if not settings.ALLOW_MARKDOWN_OUTPUT:
            raise ValueError("Markdown output is disabled by server configuration.")
        rendered = _render_markdown(envelope.model_dump())

    commit_message = f"Save analysis for {entry.file_name}"
    response = await github_client.write_text_file(
        path=output_path,
        content=rendered,
        message=commit_message,
    )

    return {
        "ok": True,
        "written_path": output_path,
        "commit_sha": response.get("commit", {}).get("sha"),
        "seq": entry.seq,
    }

@mcp.tool()
async def get_next_unprocessed_file() -> dict[str, Any]:
    """Return the next manifest entry that does not already have saved JSON output."""
    entries = await manifest_service.load_manifest()

    for internal_index, entry in enumerate(entries):
        stem = entry.file_name.rsplit(".", 1)[0]
        output_path = f"{settings.OUTPUT_FOLDER}/{stem}.json"

        if await github_client.file_exists(output_path):
            continue

        external_index = internal_index + settings.INDEX_BASE

        return {
            "found": True,
            "index": external_index,
            "seq": entry.seq,
            "path": entry.path,
            "file_name": entry.file_name,
            "output_path": output_path,
            "output_exists": False,
        }

    return {
        "found": False,
        "reason": "no_unprocessed_files",
    }

def _render_markdown(payload: dict[str, Any]) -> str:
    analysis = payload["analysis"]
    body = [
        f"# Analysis: {payload['input_file']}",
        "",
        f"- seq: {payload['seq']}",
        f"- index: {payload['index']}",
        f"- index_base: {payload['index_base']}",
        f"- input_path: `{payload['input_path']}`",
        "",
        "## Analysis",
        "",
        "```json",
        json.dumps(analysis, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(body)