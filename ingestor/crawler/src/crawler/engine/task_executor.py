"""
Task 执行器

最小执行单元，负责获取单个 Line 下的多条数据。
Task 不感知下载器实现细节，通过 CrawlerContext 获取共享资源。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from crawler.models.execution import TaskConfig, TaskResult, TaskStatus
from crawler.models.source import DataItem
from crawler.engine.context import CrawlerContext

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Task 执行器：处理单个 Line 的数据获取"""

    def __init__(self, config: TaskConfig, context: CrawlerContext) -> None:
        self.config = config
        self.context = context

    async def execute(self) -> TaskResult:
        """执行采集任务，返回结果"""
        result = TaskResult(
            task_id=self.config.task_id,
            line_id=self.config.line_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
        )

        try:
            items = await self._fetch_data()
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

    async def _fetch_data(self) -> list[DataItem]:
        """
        获取数据的核心逻辑。

        基础实现：下载 Line URL 的内容并包装为 DataItem。
        子类或具体实现可扩展此方法以支持分页、链接提取等。
        """
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

        item = DataItem(
            id=uuid.uuid4().hex[:12],
            line_id=self.config.line_id,
            source_id=self.context.config.source_id,
            url=response.url,
            title=self.config.line_name,
            content=response.text,
            content_type=response.content_type,
            raw={"status_code": response.status_code},
        )

        return [item]
