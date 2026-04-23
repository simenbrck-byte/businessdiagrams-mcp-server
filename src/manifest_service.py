from __future__ import annotations

import json

from .github_api import GithubRepoClient
from .models import ManifestEntry


class ManifestError(RuntimeError):
    pass


class ManifestService:
    def __init__(self, github_client: GithubRepoClient, manifest_path: str):
        self.github_client = github_client
        self.manifest_path = manifest_path
        self._cache: list[ManifestEntry] | None = None

    async def load_manifest(self) -> list[ManifestEntry]:
        if self._cache is not None:
            return self._cache
        raw = await self.github_client.read_text_file(self.manifest_path)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"Manifest is not valid JSON: {exc}") from exc
        if not isinstance(data, list):
            raise ManifestError("Manifest must be a JSON array of file entries.")
        entries = [ManifestEntry.model_validate(item) for item in data]
        if not entries:
            raise ManifestError("Manifest is empty.")
        seqs = [entry.seq for entry in entries]
        if len(seqs) != len(set(seqs)):
            raise ManifestError("Manifest contains duplicate seq values.")
        self._cache = entries
        return entries

    async def total_files(self) -> int:
        return len(await self.load_manifest())

    async def entry_for_external_index(self, external_index: int, index_base: int) -> tuple[int, ManifestEntry]:
        entries = await self.load_manifest()
        internal_index = external_index - index_base
        if internal_index < 0 or internal_index >= len(entries):
            raise IndexError(
                f"Index {external_index} is out of range for {len(entries)} manifest entries "
                f"with INDEX_BASE={index_base}."
            )
        return internal_index, entries[internal_index]