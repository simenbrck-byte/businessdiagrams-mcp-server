from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings


class GitHubAPIError(RuntimeError):
    pass

@dataclass(frozen=True)
class GithubFile:
    path: str
    sha: str | None
    content_bytes: bytes


class GithubRepoClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._base = "https://api.github.com"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self.settings.APP_NAME,
        }

    def _contents_url(self, path: str) -> str:
        return (
            f"{self._base}/repos/"
            f"{self.settings.GITHUB_OWNER}/{self.settings.GITHUB_REPO}/contents/{path}"
        )

    async def read_text_file(self, path: str) -> str:
        data = await self._get_contents_json(path)
        if data.get("type") != "file":
            raise GitHubAPIError(f"Expected a file at {path!r}, got: {data.get('type')!r}")
        content = data.get("content")
        encoding = data.get("encoding")
        if not content or encoding != "base64":
            raise GitHubAPIError(f"GitHub did not return base64 content for {path!r}")
        return base64.b64decode(content).decode("utf-8")

    async def read_binary_file(self, path: str) -> GithubFile:
        url = self._contents_url(path)
        params = {"ref": self.settings.GITHUB_BRANCH}
        headers = {**self._headers, "Accept": "application/vnd.github.raw"}
        async with httpx.AsyncClient(timeout=self.settings.REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise GitHubAPIError(
                f"Failed to download binary file {path!r}: "
                f"{response.status_code} {response.text}"
            )
        metadata = await self._get_contents_json(path)
        return GithubFile(path=path, sha=metadata.get("sha"), content_bytes=response.content)

    async def write_text_file(self, path: str, content: str, message: str) -> dict[str, Any]:
        url = self._contents_url(path)
        existing_sha = await self._maybe_get_sha(path)
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": self.settings.GITHUB_BRANCH,
        }
        if existing_sha:
            payload["sha"] = existing_sha
        if self.settings.COMMITTER_NAME and self.settings.COMMITTER_EMAIL:
            payload["committer"] = {
                "name": self.settings.COMMITTER_NAME,
                "email": self.settings.COMMITTER_EMAIL,
            }
        async with httpx.AsyncClient(timeout=self.settings.REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.put(url, headers=self._headers, json=payload)
        if response.status_code not in (200, 201):
            raise GitHubAPIError(f"Failed to write {path!r}: {response.status_code} {response.text}")
        return response.json()

    async def _maybe_get_sha(self, path: str) -> str | None:
        url = self._contents_url(path)
        params = {"ref": self.settings.GITHUB_BRANCH}
        async with httpx.AsyncClient(timeout=self.settings.REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=self._headers, params=params)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise GitHubAPIError(
                f"Failed to fetch metadata for {path!r}: {response.status_code} {response.text}"
            )
        data = response.json()
        return data.get("sha")

    async def _get_contents_json(self, path: str) -> dict[str, Any]:
        url = self._contents_url(path)
        params = {"ref": self.settings.GITHUB_BRANCH}
        async with httpx.AsyncClient(timeout=self.settings.REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=self._headers, params=params)
        if response.status_code != 200:
            raise GitHubAPIError(f"Failed to read {path!r}: {response.status_code} {response.text}")
        data = response.json()
        if not isinstance(data, dict):
            raise GitHubAPIError(f"Unexpected GitHub response for {path!r}")
        return data

	async def file_exists(self, path: str) -> bool:
    	return (await self._maybe_get_sha(path)) is not None
