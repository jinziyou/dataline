"""
Crawler 运行上下文

管理单个 Source 级别的共享状态，包括去重集合、下载器实例、会话与限流。
同一 Source 下的所有 Task 共享同一个 CrawlerContext。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Protocol, runtime_checkable

from crawler.models.execution import CrawlerConfig, DownloaderType
from crawler.downloaders.base import BaseDownloader
from crawler.downloaders.http import HttpDownloader

logger = logging.getLogger(__name__)


@runtime_checkable
class DeduplicationStrategy(Protocol):
    """去重策略接口"""
    def is_seen(self, key: str) -> bool: ...
    def mark_seen(self, key: str) -> None: ...
    def reset(self) -> None: ...


class UrlDeduplicator:
    """基于 URL 哈希的默认去重实现"""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_seen(self, key: str) -> bool:
        h = hashlib.md5(key.encode()).hexdigest()
        return h in self._seen

    def mark_seen(self, key: str) -> None:
        h = hashlib.md5(key.encode()).hexdigest()
        self._seen.add(h)

    def reset(self) -> None:
        self._seen.clear()


class RateLimiter:
    """简易令牌桶限流器"""

    def __init__(self, rate: float | None) -> None:
        self._rate = rate
        self._lock = asyncio.Lock()
        self._last_time: float = 0

    async def acquire(self) -> None:
        if self._rate is None:
            return
        async with self._lock:
            loop = asyncio.get_event_loop()
            now = loop.time()
            interval = 1.0 / self._rate
            wait = self._last_time + interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_time = asyncio.get_event_loop().time()


class CrawlerContext:
    """
    Crawler 运行上下文容器。

    管理单个 Source 的所有共享状态：
    - 下载器实例（根据配置选择 HTTP/Playwright 等）
    - 去重策略
    - 限流器
    - 并发控制信号量
    """

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config
        self._downloader: BaseDownloader | None = None
        self._dedup: DeduplicationStrategy = UrlDeduplicator()
        self._rate_limiter = RateLimiter(config.rate_limit)
        self._semaphore = asyncio.Semaphore(config.concurrency)

    def _create_downloader(self) -> BaseDownloader:
        if self.config.downloader == DownloaderType.PLAYWRIGHT:
            logger.warning(
                "Playwright downloader not yet implemented, falling back to HTTP"
            )
        return HttpDownloader(
            default_headers=self.config.headers,
            timeout=self.config.timeout,
        )

    @property
    def downloader(self) -> BaseDownloader:
        if self._downloader is None:
            self._downloader = self._create_downloader()
        return self._downloader

    @property
    def dedup(self) -> DeduplicationStrategy:
        return self._dedup

    @property
    def rate_limiter(self) -> RateLimiter:
        return self._rate_limiter

    @property
    def semaphore(self) -> asyncio.Semaphore:
        return self._semaphore

    async def close(self) -> None:
        if self._downloader is not None:
            await self._downloader.close()
            self._downloader = None

    async def __aenter__(self) -> CrawlerContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
