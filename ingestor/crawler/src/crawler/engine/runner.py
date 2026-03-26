"""
CrawlerRunner

Crawler 的顶层运行入口，管理整个采集流程：
1. 根据 CrawlerConfig 创建 CrawlerContext
2. 为每个 TaskConfig 创建 TaskExecutor
3. 并发执行所有 Task 并收集结果
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from crawler.models.execution import CrawlerConfig, CrawlerResult
from crawler.engine.context import CrawlerContext
from crawler.engine.task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class CrawlerRunner:
    """
    Crawler 运行器。

    库调用入口示例::

        config = generate_crawler_config(source, lines)
        runner = CrawlerRunner(config)
        result = await runner.run()
    """

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config

    async def run(self) -> CrawlerResult:
        """执行整个 crawler 的采集流程"""
        result = CrawlerResult(
            crawler_id=self.config.crawler_id,
            source_id=self.config.source_id,
            started_at=datetime.now(),
        )

        logger.info(
            "Crawler %s started for source %s with %d tasks",
            self.config.crawler_id,
            self.config.source_id,
            len(self.config.tasks),
        )

        async with CrawlerContext(self.config) as context:
            executors = [
                TaskExecutor(task_config, context)
                for task_config in self.config.tasks
            ]

            task_results = await asyncio.gather(
                *(executor.execute() for executor in executors),
                return_exceptions=False,
            )

            result.task_results = list(task_results)

        result.finished_at = datetime.now()
        logger.info(
            "Crawler %s finished: %d items, %d success, %d failed",
            self.config.crawler_id,
            result.total_items,
            result.success_count,
            result.failed_count,
        )

        return result
