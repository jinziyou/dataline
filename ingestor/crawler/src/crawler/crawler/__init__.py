"""
crawler 子包：crawler -> task -> data 执行侧对象

``Crawler`` 为功能主入口（``run_source`` / ``from_source``）；其余为配置与执行单元模型。
"""

from crawler.crawler.crawler import (
    SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY,
    Crawler,
    CrawlerBuildOptions,
    CrawlerConfig,
    CrawlerContext,
    CrawlerResult,
    DownloaderType,
    DeduplicationStrategy,
    RateLimiter,
    UrlDeduplicator,
    build_crawler_config,
    task_config_from_line,
)
from crawler.crawler.data import Data
from crawler.crawler.extractor import Extractor, PageExtractor
from crawler.crawler.task import TaskConfig, TaskExecutor, TaskResult, TaskStatus

__all__ = [
    "SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY",
    "Crawler",
    "CrawlerBuildOptions",
    "CrawlerConfig",
    "CrawlerContext",
    "CrawlerResult",
    "Data",
    "DownloaderType",
    "DeduplicationStrategy",
    "Extractor",
    "PageExtractor",
    "RateLimiter",
    "TaskConfig",
    "TaskExecutor",
    "TaskResult",
    "TaskStatus",
    "UrlDeduplicator",
    "build_crawler_config",
    "task_config_from_line",
]
