"""
最小执行单元：Task

对应 Line 的配置、执行结果与 TaskExecutor。
TaskExecutor 通过 Extractor 管线（LinkExtractor → DataExtractor）将响应转为多条 Data。
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

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
    title/time/content_selector 对应 DataExtractor（最终数据页）。
    """
    link_selectors: list[str] = Field(
        default_factory=list,
        description="链接提取选择器列表，按层级顺序",
    )
    title_selector: str | None = Field(default=None, description="标题 CSS 选择器")
    time_selector: str | None = Field(default=None, description="时间 CSS 选择器")
    content_selector: str | None = Field(default=None, description="正文 CSS 选择器")

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

        await self.context.rate_limiter.acquire()

        if (
            self.context.config.dedup_enabled
            and self.context.dedup.is_seen(url)
        ):
            logger.debug("URL already seen, skipping: %s", url)
            return []

        async with self.context.semaphore:
            response = await self.context.downloader.download(
                url, timeout=self.context.config.timeout,
            )

        self.context.dedup.mark_seen(url)

        return await self._data_extractor.extract(
            response=response,
            line_id=self.config.line_id,
            source_id=self.context.config.source_id,
            line_name=self.config.line_name,
            task_id=self.config.task_id,
        )

    async def _fetch_via_links(self) -> list[Data]:
        """多级链接提取 → 数据提取管线。"""
        urls = [self.config.url]

        for link_extractor in self._link_extractors:
            next_urls: list[str] = []
            for url in urls:
                if url is None:
                    continue
                response = await self._download(url)
                found = await link_extractor.extract_links(response, base_url=url)
                next_urls.extend(found)
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

    async def _download(self, url: str) -> DownloadResponse:
        """带限流和并发控制的下载。"""
        await self.context.rate_limiter.acquire()
        async with self.context.semaphore:
            return await self.context.downloader.download(
                url, timeout=self.context.config.timeout,
            )
