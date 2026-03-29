"""
crawler - 多源异类数据采集引擎

领域模型为 ``Source``（内含 ``lines``）与 ``Line``；执行入口为 ``Crawler``
（推荐 ``await Crawler.run_source(source)``；数据源级采集默认项见 ``SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY``，并与类型预设、``options`` / ``overrides`` 合并）。
底层 ``build_crawler_config`` 等仍可按需直接使用。
"""

from crawler.crawler import (
    SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY,
    Crawler,
    CrawlerBuildOptions,
    CrawlerConfig,
    CrawlerContext,
    CrawlerResult,
    Data,
    DownloaderType,
    Extractor,
    PageExtractor,
    TaskConfig,
    TaskExecutor,
    TaskResult,
    TaskStatus,
    build_crawler_config,
    task_config_from_line,
)
from crawler.source import Line, Source, SourceType

DataItem = Data
CrawlerRunner = Crawler

__all__ = [
    "SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY",
    "Crawler",
    "CrawlerBuildOptions",
    "CrawlerConfig",
    "CrawlerContext",
    "CrawlerResult",
    "CrawlerRunner",
    "Data",
    "DataItem",
    "DownloaderType",
    "Extractor",
    "Line",
    "PageExtractor",
    "Source",
    "SourceType",
    "TaskConfig",
    "TaskExecutor",
    "TaskResult",
    "TaskStatus",
    "build_crawler_config",
    "task_config_from_line",
]
