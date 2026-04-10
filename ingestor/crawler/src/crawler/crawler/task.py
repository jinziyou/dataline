"""
最小执行单元：Task

对应 Line 的配置、执行结果与 TaskExecutor。
TaskExecutor 通过 Extractor 管线（LinkExtractor → DataExtractor）将响应转为多条 Data。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from crawler.crawler.crawler import CrawlerContext
from crawler.crawler.data import Data
from crawler.crawler.downloaders.base import DownloadResponse
from crawler.crawler.extractor import (
    DataExtractor,
    Extractor,
    LinkExtractor,
    PageExtractor,
)


class DownloadError(Exception):
    """下载失败异常（HTTP 错误状态码或网络错误）"""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExtractorConfig(BaseModel):
    """
    提取器配置：描述一个 Task 的提取管线。

    link_selectors 按层级顺序对应多个 LinkExtractor（列表页 → 子列表页 → …）；
    title/time/content_selector 对应 DataExtractor（最终数据页）；
    next_page_selector 配置后自动翻页，max_pages 限制最大翻页数。
    """
    link_selectors: list[str] = Field(
        default_factory=list,
        description="链接提取选择器列表，按层级顺序",
    )
    title_selector: str | None = Field(default=None, description="标题 CSS 选择器")
    time_selector: str | None = Field(default=None, description="时间 CSS 选择器")
    content_selector: str | None = Field(default=None, description="正文 CSS 选择器")
    next_page_selector: str | None = Field(
        default=None,
        description="下一页链接选择器（配置后在每层链接提取时自动翻页）",
    )
    max_pages: int | None = Field(
        default=None,
        description="最大翻页数（含首页），None 表示不限制",
    )

    @property
    def has_data_selectors(self) -> bool:
        return any([self.title_selector, self.time_selector, self.content_selector])


class TaskConfig(BaseModel):
    """采集任务配置：对应一个 Line"""
    task_id: str = Field(description="任务 ID")
    line_id: str = Field(description="对应的 Line ID")
    line_name: str = Field(default="", description="对应的 Line 名称")
    url: str | None = Field(default=None, description="采集入口地址")
    params: dict[str, Any] = Field(default_factory=dict, description="任务级参数")
    max_items: int | None = Field(default=None, description="最大采集条数限制")
    extractors: ExtractorConfig = Field(
        default_factory=ExtractorConfig,
        description="提取器配置（链接选择器 + 数据选择器）",
    )


class TaskResult(BaseModel):
    """单个 Task 的执行结果"""
    task_id: str
    line_id: str
    status: TaskStatus = TaskStatus.PENDING
    items: list[Data] = Field(default_factory=list)
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def item_count(self) -> int:
        return len(self.items)


class TaskExecutor:
    """
    Task 执行器：处理单个 Line 的数据获取。

    执行管线：
    - 若存在 link_extractors：列表页 → 链接发现（可多级） → 逐个详情页数据提取
    - 否则：直接用 data_extractor 提取当前页
    """

    def __init__(
        self,
        config: TaskConfig,
        context: CrawlerContext,
        *,
        link_extractors: list[LinkExtractor] | None = None,
        data_extractor: Extractor | None = None,
        extractor: Extractor | None = None,
    ) -> None:
        self.config = config
        self.context = context

        if link_extractors is not None:
            self._link_extractors = link_extractors
        else:
            self._link_extractors = [
                LinkExtractor(selector=s)
                for s in config.extractors.link_selectors
            ]

        effective_data = data_extractor or extractor
        if effective_data is not None:
            self._data_extractor: Extractor = effective_data
        elif config.extractors.has_data_selectors:
            self._data_extractor = DataExtractor(
                title_selector=config.extractors.title_selector,
                time_selector=config.extractors.time_selector,
                content_selector=config.extractors.content_selector,
            )
        else:
            self._data_extractor = PageExtractor()

    async def execute(self) -> TaskResult:
        result = TaskResult(
            task_id=self.config.task_id,
            line_id=self.config.line_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
        )

        try:
            items = await self._fetch_data()
            if self.config.max_items is not None:
                items = items[: self.config.max_items]
            result.items = items
            result.status = TaskStatus.SUCCESS
            logger.info(
                "Task %s completed: %d items collected",
                self.config.task_id,
                len(items),
            )
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            logger.error("Task %s failed: %s", self.config.task_id, e)
        finally:
            result.finished_at = datetime.now()

        return result

    async def _fetch_data(self) -> list[Data]:
        if not self.config.url:
            logger.warning("Task %s has no URL, skipping", self.config.task_id)
            return []

        if self._link_extractors:
            return await self._fetch_via_links()
        return await self._fetch_direct()

    async def _fetch_direct(self) -> list[Data]:
        """直接从 URL 提取数据（无链接层级，向后兼容原流程）。"""
        url = self.config.url
        assert url is not None

        # 先检查去重，避免对已见 URL 触发限流
        if self.context.config.dedup_enabled and self.context.dedup.is_seen(url):
            logger.debug("URL already seen, skipping: %s", url)
            return []

        response = await self._download(url)
        self.context.dedup.mark_seen(url)

        return await self._data_extractor.extract(
            response=response,
            line_id=self.config.line_id,
            source_id=self.context.config.source_id,
            line_name=self.config.line_name,
            task_id=self.config.task_id,
        )

    async def _fetch_via_links(self) -> list[Data]:
        """多级链接提取 → 数据提取管线（支持自动翻页）。"""
        urls: list[str | None] = [self.config.url]

        for link_extractor in self._link_extractors:
            next_urls: list[str] = []
            for url in urls:
                if url is None:
                    continue
                page_links = await self._collect_paginated_links(url, link_extractor)
                next_urls.extend(page_links)
            urls = next_urls  # type: ignore[assignment]

        all_items: list[Data] = []
        for url in urls:
            if self.config.max_items is not None and len(all_items) >= self.config.max_items:
                break

            if self.context.config.dedup_enabled and self.context.dedup.is_seen(url):
                logger.debug("URL already seen, skipping: %s", url)
                continue

            response = await self._download(url)
            self.context.dedup.mark_seen(url)

            items = await self._data_extractor.extract(
                response=response,
                line_id=self.config.line_id,
                source_id=self.context.config.source_id,
                line_name=self.config.line_name,
                task_id=self.config.task_id,
            )
            all_items.extend(items)

        return all_items

    async def _collect_paginated_links(
        self,
        start_url: str,
        link_extractor: LinkExtractor,
    ) -> list[str]:
        """
        从起始 URL 收集链接，配置了 next_page_selector 时自动跟随翻页。

        翻页终止条件：
        - 找不到下一页链接
        - 下一页 URL 已访问过（防循环）
        - 已达 max_pages 上限
        """
        all_links: list[str] = []
        next_page_selector = self.config.extractors.next_page_selector
        max_pages = self.config.extractors.max_pages
        current_url: str | None = start_url
        page_count = 0
        visited_pages: set[str] = set()

        while current_url is not None:
            if current_url in visited_pages:
                logger.debug("Pagination loop detected, stopping at: %s", current_url)
                break
            if max_pages is not None and page_count >= max_pages:
                logger.debug("Reached max_pages=%d, stopping pagination", max_pages)
                break

            visited_pages.add(current_url)
            page_count += 1

            response = await self._download(current_url)
            links = await link_extractor.extract_links(response, base_url=current_url)
            all_links.extend(links)
            logger.debug(
                "Pagination page %d (%s): found %d links",
                page_count, current_url, len(links),
            )

            if not next_page_selector:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            next_el = soup.select_one(next_page_selector)
            if not next_el:
                break
            href = next_el.get("href")
            if not href or not isinstance(href, str) or not href.strip():
                break
            current_url = urljoin(current_url, href.strip())

        return all_links

    async def _download(self, url: str) -> DownloadResponse:
        """带限流、并发控制和自动重试的下载。

        重试策略：
        - HTTP 4xx：不重试（客户端错误），立即抛出 DownloadError
        - HTTP 5xx：重试（服务端错误，可能是临时故障）
        - 网络异常：重试
        """
        retry_max = self.context.config.retry_max
        retry_delay = self.context.config.retry_delay
        last_exc: Exception | None = None

        for attempt in range(retry_max + 1):
            if attempt > 0:
                logger.warning(
                    "Task %s: retry %d/%d for %s",
                    self.config.task_id, attempt, retry_max, url,
                )
                await asyncio.sleep(retry_delay)
            await self.context.rate_limiter.acquire()
            try:
                async with self.context.semaphore:
                    response = await self.context.downloader.download(
                        url, timeout=self.context.config.timeout,
                    )
                if 400 <= response.status_code < 500:
                    raise DownloadError(
                        f"HTTP {response.status_code}: {url}",
                        status_code=response.status_code,
                    )
                if response.status_code >= 500:
                    last_exc = DownloadError(
                        f"HTTP {response.status_code}: {url}",
                        status_code=response.status_code,
                    )
                    continue
                return response
            except DownloadError:
                raise
            except Exception as e:
                last_exc = e

        raise last_exc or DownloadError(f"Download failed after {retry_max + 1} attempt(s): {url}")
