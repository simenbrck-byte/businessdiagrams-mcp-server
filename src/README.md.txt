# GitHub Batch MCP Server for Render

This repository contains a Python MCP server for the exact flow you described:

- **Agent 1** calls an MCP tool to get the total number of files.
- A **while loop node** uses that integer as the upper bound.
- **Agent 2** runs inside the loop, and on each iteration:
  - calls an MCP tool to fetch exactly one PNG by index,
  - analyzes only that file,
  - calls an MCP tool to save the analysis result back to GitHub.

The server uses the official Python MCP SDK and is mounted over **streamable HTTP** inside a FastAPI app so it can be deployed as a normal **Render Web Service**.

## MCP tools exposed

### `get_total_files() -> int`
Returns the number of files in the configured manifest.

### `get_file_by_index(index: int) -> Image`
Returns exactly one PNG image from the manifest as an MCP `Image`.

The index convention is controlled by `INDEX_BASE`:

- `INDEX_BASE=0` → valid indexes are `0..N-1`
- `INDEX_BASE=1` → valid indexes are `1..N`

### `save_analysis_result(index: int, analysis: dict, output_format: "json" | "markdown" = "json") -> dict`
Writes the worker agent's result into the configured `OUTPUT_FOLDER`.

The output file name is derived from the indexed manifest row. The worker agent does **not** need to know the GitHub path or original filename.

## Repository assumptions

This server targets a content repository with at least:

```text
manifests/input_manifest.json
input/...
output/...