"""测试用桩实现（无网络）。"""

from __future__ import annotations

from crawler.crawler.downloaders.base import BaseDownloader, DownloadResponse


class StubDownloader(BaseDownloader):
    """按 URL 返回固定响应，不发起网络请求。"""

    def __init__(
        self,
        *,
        text: str = "<html>ok</html>",
        status_code: int = 200,
        content_type: str = "text/html",
    ) -> None:
        self._text = text
        self._status_code = status_code
        self._content_type = content_type
        self.urls: list[str] = []

    async def download(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> DownloadResponse:
        _ = headers, timeout
        self.urls.append(url)
        body = self._text.encode()
        return DownloadResponse(
            url=url,
            status_code=self._status_code,
            content=body,
            text=self._text,
            headers={},
            content_type=self._content_type,
        )

    async def close(self) -> None:
        pass
