"""
最小执行单元：Task

对应 Line 的配置、执行结果与 TaskExecutor；通过 Extractor 将响应转为多条 Data。
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from crawler.crawler.crawler import CrawlerContext
from crawler.crawler.data import Data
from crawler.crawler.extractor import Extractor, PageExtractor

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskConfig(BaseModel):
    """采集任务配置：对应一个 Line"""
    task_id: str = Field(description="任务 ID")
    line_id: str = Field(description="对应的 Line ID")
    line_name: str = Field(default="", description="对应的 Line 名称")
    url: str | None = Field(default=None, description="采集入口地址")
    params: dict[str, Any] = Field(default_factory=dict, description="任务级参数")
    max_items: int | None = Field(default=None, description="最大采集条数限制")


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
    """Task 执行器：处理单个 Line 的数据获取"""

    def __init__(
        self,
        config: TaskConfig,
        context: CrawlerContext,
        *,
        extractor: Extractor | None = None,
    ) -> None:
        self.config = config
        self.context = context
        self._extractor: Extractor = extractor or PageExtractor()

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

        await self.context.rate_limiter.acquire()

        if (
            self.context.config.dedup_enabled
            and self.context.dedup.is_seen(self.config.url)
        ):
            logger.debug("URL already seen, skipping: %s", self.config.url)
            return []

        async with self.context.semaphore:
            response = await self.context.downloader.download(
                self.config.url,
                timeout=self.context.config.timeout,
            )

        self.context.dedup.mark_seen(self.config.url)

        return await self._extractor.extract(
            response=response,
            line_id=self.config.line_id,
            source_id=self.context.config.source_id,
            line_name=self.config.line_name,
            task_id=self.config.task_id,
        )
