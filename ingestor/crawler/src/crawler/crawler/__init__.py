"""
crawler 子包：crawler -> task -> extractor 执行侧对象

``Crawler`` 为功能主入口（``run_source`` / ``from_source``）；其余为配置与执行单元模型。
"""

from crawler.crawler.crawler import (
    EXTRACTOR_CONFIG_META_KEY,
    SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY,
    Crawler,
    CrawlerBuildOptions,
    CrawlerConfig,
    CrawlerContext,
    CrawlerResult,
    DeduplicationStrategy,
    DownloaderType,
    RateLimiter,
    UrlDeduplicator,
    build_crawler_config,
    task_config_from_line,
)
from crawler.crawler.data import Data
from crawler.crawler.density import (
    DensityBasedDetector,
    DetectedSelectors,
    SelectorDetector,
)
from crawler.crawler.extractor import (
    DataExtractor,
    Extractor,
    LinkExtractor,
    PageExtractor,
)
from crawler.crawler.task import (
    DownloadError,
    ExtractorConfig,
    TaskConfig,
    TaskExecutor,
    TaskResult,
    TaskStatus,
)

__all__ = [
    "EXTRACTOR_CONFIG_META_KEY",
    "SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY",
    "Crawler",
    "CrawlerBuildOptions",
    "CrawlerConfig",
    "CrawlerContext",
    "CrawlerResult",
    "Data",
    "DataExtractor",
    "DeduplicationStrategy",
    "DownloadError",
    "DensityBasedDetector",
    "DetectedSelectors",
    "DownloaderType",
    "Extractor",
    "ExtractorConfig",
    "LinkExtractor",
    "PageExtractor",
    "RateLimiter",
    "SelectorDetector",
    "TaskConfig",
    "TaskExecutor",
    "TaskResult",
    "TaskStatus",
    "UrlDeduplicator",
    "build_crawler_config",
    "task_config_from_line",
]
