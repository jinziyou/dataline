"""
crawler - 多源异类数据采集引擎

提供 source->line->data 统一数据抽象与 crawler->task->data 执行模型，
支持以库调用或命令行工具方式对外提供采集能力。
"""

from crawler.models.source import Source, Line, DataItem, SourceType
from crawler.models.execution import CrawlerConfig, TaskConfig, TaskResult, CrawlerResult
from crawler.engine.runner import CrawlerRunner

__all__ = [
    "Source",
    "Line",
    "DataItem",
    "SourceType",
    "CrawlerConfig",
    "TaskConfig",
    "TaskResult",
    "CrawlerResult",
    "CrawlerRunner",
]
