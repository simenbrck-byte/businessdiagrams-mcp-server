from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class ManifestEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    seq: int = Field(..., description="Sequential identifier from the manifest.")
    path: str = Field(..., description="Path to the input file in the GitHub repository.")
    file_name: str = Field(..., description="Input file name.")


class SavedAnalysisEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    seq: int
    index: int
    index_base: int
    input_file: str
    input_path: str
    content_repo: str
    content_branch: str
    output_format: Literal["json", "markdown"]
    analysis: Any