"""
crawler - 多源异类数据采集引擎

领域模型为 ``Source``（内含 ``lines``）与 ``Line``；执行入口为 ``Crawler``
（推荐 ``await Crawler.run_source(source)``）。

Extractor 管线：``LinkExtractor``（链接发现，一个或多个）→ ``DataExtractor``（数据提取）。
``DensityBasedDetector`` 可自动从页面推导选择器。
"""

from crawler.crawler import (
    EXTRACTOR_CONFIG_META_KEY,
    SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY,
    Crawler,
    CrawlerBuildOptions,
    CrawlerConfig,
    CrawlerContext,
    CrawlerResult,
    Data,
    DataExtractor,
    DensityBasedDetector,
    DetectedSelectors,
    DownloaderType,
    Extractor,
    ExtractorConfig,
    LinkExtractor,
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
    "EXTRACTOR_CONFIG_META_KEY",
    "SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY",
    "Crawler",
    "CrawlerBuildOptions",
    "CrawlerConfig",
    "CrawlerContext",
    "CrawlerResult",
    "CrawlerRunner",
    "Data",
    "DataExtractor",
    "DataItem",
    "DensityBasedDetector",
    "DetectedSelectors",
    "DownloaderType",
    "Extractor",
    "ExtractorConfig",
    "Line",
    "LinkExtractor",
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
