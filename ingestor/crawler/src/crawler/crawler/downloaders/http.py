"""
HTTP 下载器

基于 httpx 的异步 HTTP 下载器实现。
"""

from __future__ import annotations

import httpx

from crawler.crawler.downloaders.base import BaseDownloader, DownloadResponse


class HttpDownloader(BaseDownloader):
    """基于 httpx 的 HTTP 下载器"""

    def __init__(
        self,
        *,
        default_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
    ) -> None:
        self._client = httpx.AsyncClient(
            headers=default_headers or {},
            timeout=httpx.Timeout(timeout),
            follow_redirects=follow_redirects,
        )

    async def download(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> DownloadResponse:
        response = await self._client.get(
            url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )
        return DownloadResponse(
            url=str(response.url),
            status_code=response.status_code,
            content=response.content,
            text=response.text,
            headers=dict(response.headers),
            content_type=response.headers.get("content-type", ""),
        )

    async def close(self) -> None:
        await self._client.aclose()
