"""
下载器抽象基类

定义下载器的统一接口，供不同下载策略（HTTP、Playwright 等）实现。
Task 无需感知具体下载器实现，统一通过此接口获取数据。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DownloadResponse:
    """下载响应"""
    url: str
    status_code: int
    content: bytes
    text: str
    headers: dict[str, str]
    content_type: str


class BaseDownloader(ABC):
    """下载器抽象基类"""

    @abstractmethod
    async def download(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> DownloadResponse:
        """下载指定 URL 的内容"""
        ...

    @abstractmethod
    async def close(self) -> None:
        """释放下载器资源"""
        ...

    async def __aenter__(self) -> BaseDownloader:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
