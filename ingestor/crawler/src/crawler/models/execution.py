"""
执行模型：crawler -> task -> data

将数据采集过程抽象为执行结构，与数据抽象模型一一映射：
- CrawlerConfig: 对应 Source，采集运行容器的配置
- TaskConfig:    对应 Line，最小执行单元的配置
- TaskResult:    单个 task 的执行结果
- CrawlerResult: 整个 crawler 的执行结果
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from crawler.models.source import DataItem


class DownloaderType(str, Enum):
    """下载器类型"""
    HTTP = "http"
    PLAYWRIGHT = "playwright"


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


class CrawlerConfig(BaseModel):
    """采集运行容器配置：对应一个 Source"""
    crawler_id: str = Field(description="Crawler ID")
    source_id: str = Field(description="对应的 Source ID")
    source_name: str = Field(default="", description="对应的 Source 名称")
    downloader: DownloaderType = Field(default=DownloaderType.HTTP, description="下载器类型")
    tasks: list[TaskConfig] = Field(default_factory=list, description="下属 Task 列表")

    headers: dict[str, str] = Field(default_factory=dict, description="公共请求头")
    timeout: float = Field(default=30.0, description="请求超时（秒）")
    retry_max: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试间隔（秒）")
    concurrency: int = Field(default=5, description="并发数")
    rate_limit: float | None = Field(default=None, description="请求速率限制（次/秒），None 不限")
    dedup_enabled: bool = Field(default=True, description="是否启用去重")

    meta: dict[str, Any] = Field(default_factory=dict, description="扩展配置")


class TaskResult(BaseModel):
    """单个 Task 的执行结果"""
    task_id: str
    line_id: str
    status: TaskStatus = TaskStatus.PENDING
    items: list[DataItem] = Field(default_factory=list)
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def item_count(self) -> int:
        return len(self.items)


class CrawlerResult(BaseModel):
    """整个 Crawler 的执行结果"""
    crawler_id: str
    source_id: str
    task_results: list[TaskResult] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def total_items(self) -> int:
        return sum(r.item_count for r in self.task_results)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == TaskStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == TaskStatus.FAILED)
