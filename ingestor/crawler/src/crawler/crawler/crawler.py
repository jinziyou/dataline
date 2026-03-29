"""
运行容器：Crawler

对应 Source 级别的采集配置与执行入口，管理共享上下文（去重、下载器、限流、并发）。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Iterable, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from crawler.crawler.downloaders.base import BaseDownloader
from crawler.crawler.downloaders.http import HttpDownloader
from crawler.source.line import Line
from crawler.source.source import Source

logger = logging.getLogger(__name__)

# Source.meta 中存放与 CrawlerBuildOptions 字段兼容的字典；仅 crawler 层解释，source 领域模型不声明该键。
SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY = "crawler_build_options"


class DownloaderType(str, Enum):
    """下载器类型"""
    HTTP = "http"
    PLAYWRIGHT = "playwright"


class CrawlerConfig(BaseModel):
    """采集运行容器配置：对应一个 Source（tasks 对应多个 Line）"""
    crawler_id: str = Field(description="Crawler ID")
    source_id: str = Field(description="对应的 Source ID")
    source_name: str = Field(default="", description="对应的 Source 名称")
    downloader: DownloaderType = Field(default=DownloaderType.HTTP, description="下载器类型")
    tasks: list["TaskConfig"] = Field(default_factory=list, description="下属 Task 列表")

    headers: dict[str, str] = Field(default_factory=dict, description="公共请求头")
    timeout: float = Field(default=30.0, description="请求超时（秒）")
    retry_max: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试间隔（秒）")
    concurrency: int = Field(default=5, description="并发数")
    rate_limit: float | None = Field(default=None, description="请求速率限制（次/秒），None 不限")
    dedup_enabled: bool = Field(default=True, description="是否启用去重")

    meta: dict[str, Any] = Field(default_factory=dict, description="扩展配置")


class CrawlerBuildOptions(BaseModel):
    """
    构建 CrawlerConfig 时的可选覆盖项（相对按 Source.type 的预设）。

    凡字段为 None 表示不覆盖，仍用预设。
    """

    model_config = ConfigDict(extra="ignore")

    downloader: DownloaderType | None = None
    headers: dict[str, str] | None = None
    timeout: float | None = None
    retry_max: int | None = None
    retry_delay: float | None = None
    concurrency: int | None = None
    rate_limit: float | None = None
    dedup_enabled: bool | None = None


class CrawlerResult(BaseModel):
    """整个 Crawler 的执行结果"""
    crawler_id: str
    source_id: str
    task_results: list["TaskResult"] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def total_items(self) -> int:
        return sum(r.item_count for r in self.task_results)

    @property
    def success_count(self) -> int:
        from crawler.crawler.task import TaskStatus

        return sum(1 for r in self.task_results if r.status == TaskStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        from crawler.crawler.task import TaskStatus

        return sum(1 for r in self.task_results if r.status == TaskStatus.FAILED)


@runtime_checkable
class DeduplicationStrategy(Protocol):
    """去重策略接口"""

    def is_seen(self, key: str) -> bool: ...
    def mark_seen(self, key: str) -> None: ...
    def reset(self) -> None: ...


class UrlDeduplicator:
    """基于 URL 哈希的默认去重实现"""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_seen(self, key: str) -> bool:
        h = hashlib.md5(key.encode()).hexdigest()
        return h in self._seen

    def mark_seen(self, key: str) -> None:
        h = hashlib.md5(key.encode()).hexdigest()
        self._seen.add(h)

    def reset(self) -> None:
        self._seen.clear()


class RateLimiter:
    """简易令牌桶限流器"""

    def __init__(self, rate: float | None) -> None:
        self._rate = rate
        self._lock = asyncio.Lock()
        self._last_time: float = 0

    async def acquire(self) -> None:
        if self._rate is None:
            return
        async with self._lock:
            loop = asyncio.get_event_loop()
            now = loop.time()
            interval = 1.0 / self._rate
            wait = self._last_time + interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_time = asyncio.get_event_loop().time()


class CrawlerContext:
    """
    Crawler 运行上下文。

    管理单个 Source 的共享状态：下载器、去重、限流、并发信号量。
    """

    def __init__(
        self,
        config: CrawlerConfig,
        *,
        downloader: BaseDownloader | None = None,
    ) -> None:
        self.config = config
        self._downloader: BaseDownloader | None = downloader
        self._dedup: DeduplicationStrategy = UrlDeduplicator()
        self._rate_limiter = RateLimiter(config.rate_limit)
        self._semaphore = asyncio.Semaphore(config.concurrency)

    def _create_downloader(self) -> BaseDownloader:
        if self.config.downloader == DownloaderType.PLAYWRIGHT:
            logger.warning(
                "Playwright downloader not yet implemented, falling back to HTTP"
            )
        return HttpDownloader(
            default_headers=self.config.headers,
            timeout=self.config.timeout,
        )

    @property
    def downloader(self) -> BaseDownloader:
        if self._downloader is None:
            self._downloader = self._create_downloader()
        return self._downloader

    @property
    def dedup(self) -> DeduplicationStrategy:
        return self._dedup

    @property
    def rate_limiter(self) -> RateLimiter:
        return self._rate_limiter

    @property
    def semaphore(self) -> asyncio.Semaphore:
        return self._semaphore

    async def close(self) -> None:
        if self._downloader is not None:
            await self._downloader.close()
            self._downloader = None

    async def __aenter__(self) -> CrawlerContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


class Crawler:
    """
    采集能力与功能入口：对应单个 Source 下所有 Task 的执行。

    推荐从领域模型启动（核心入口）；``Source`` 应携带 ``lines``。若需在数据源上挂接采集引擎默认项，将兼容 ``CrawlerBuildOptions`` 的字典放在 ``source.meta[SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY]``；当次运行仍可用 ``options`` / ``overrides`` 再覆盖::

        result = await Crawler.run_source(source, overrides={...})

    或先得到实例再执行::

        crawler = Crawler.from_source(source)
        result = await crawler.run()

    已有序列化配置（如 JSON）时可直接构造::

        result = await Crawler(CrawlerConfig.model_validate(data)).run()
    """

    def __init__(
        self,
        config: CrawlerConfig,
        *,
        downloader: BaseDownloader | None = None,
    ) -> None:
        self.config = config
        self._downloader = downloader

    @classmethod
    def from_source(
        cls,
        source: Source,
        lines: Iterable[Line] | None = None,
        *,
        options: CrawlerBuildOptions | None = None,
        overrides: dict[str, Any] | None = None,
        downloader: BaseDownloader | None = None,
    ) -> Crawler:
        """由 ``Source``（含 ``lines``，或可传入 ``lines`` 覆盖当次列表）构建配置并返回实例。"""
        config = build_crawler_config(
            source,
            lines,
            options=options,
            overrides=overrides,
        )
        return cls(config, downloader=downloader)

    @classmethod
    async def run_source(
        cls,
        source: Source,
        lines: Iterable[Line] | None = None,
        *,
        options: CrawlerBuildOptions | None = None,
        overrides: dict[str, Any] | None = None,
        downloader: BaseDownloader | None = None,
    ) -> CrawlerResult:
        """一站式入口：传入 ``Source``（及可选当次 ``lines``），合并默认与额外配置后执行采集。"""
        crawler = cls.from_source(
            source,
            lines,
            options=options,
            overrides=overrides,
            downloader=downloader,
        )
        return await crawler.run()

    async def run(self) -> CrawlerResult:
        from crawler.crawler.task import TaskExecutor

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

        async with CrawlerContext(self.config, downloader=self._downloader) as context:
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


def task_config_from_line(line: Line) -> "TaskConfig":
    """由 Line 生成 TaskConfig；``line.item_limit`` 映射为任务级条数上限。"""
    import uuid

    from crawler.crawler.task import TaskConfig

    return TaskConfig(
        task_id=f"task-{uuid.uuid4().hex[:12]}",
        line_id=line.id,
        line_name=line.name,
        url=line.url,
        params=dict(line.meta),
        max_items=line.item_limit,
    )


def _merged_build_options(
    source: Source,
    options: CrawlerBuildOptions | None,
) -> CrawlerBuildOptions | None:
    """``source.meta`` 中采集引擎默认项与本次 ``options`` 合并（后者覆盖前者；``headers`` 逐键合并）。"""
    block = source.meta.get(SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY)
    raw = dict(block) if isinstance(block, dict) else {}
    headers: dict[str, str] = dict(raw.pop("headers", None) or {})

    if options is not None:
        od = options.model_dump(exclude_none=True)
        h2 = od.pop("headers", None)
        if h2:
            headers.update(h2)
        raw.update(od)

    if headers:
        raw["headers"] = headers
    if not raw:
        return None
    return CrawlerBuildOptions.model_validate(raw)


def build_crawler_config(
    source: Source,
    lines: Iterable[Line] | None = None,
    *,
    options: CrawlerBuildOptions | None = None,
    overrides: dict[str, Any] | None = None,
) -> CrawlerConfig:
    """
    根据 ``Source`` 构建 ``CrawlerConfig``。

    ``lines`` 为 ``None`` 时使用 ``source.lines``；否则使用传入列表（便于临时覆盖当次任务集）。

    优先级：``overrides`` > 本次 ``options`` > ``source.meta[SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY]`` > 按 ``source.type`` 的预设。
    """
    import uuid

    from crawler.source.presets import get_preset

    preset = get_preset(source.type)
    overrides = overrides or {}
    effective_lines = list(lines) if lines is not None else list(source.lines)
    merged_options = _merged_build_options(source, options)

    tasks = [task_config_from_line(ln) for ln in effective_lines if ln.enabled]

    def pick[T](key: str, fallback: T) -> T:
        if key in overrides:
            return overrides[key]  # type: ignore[no-any-return]
        if merged_options is not None:
            v = getattr(merged_options, key)
            if v is not None:
                return v  # type: ignore[no-any-return]
        return fallback

    headers: dict[str, str] = {**preset.headers}
    if merged_options is not None and merged_options.headers is not None:
        headers.update(merged_options.headers)
    headers.update(overrides.get("headers", {}))

    return CrawlerConfig(
        crawler_id=f"crawler-{uuid.uuid4().hex[:12]}",
        source_id=source.id,
        source_name=source.name,
        downloader=pick("downloader", DownloaderType(preset.downloader)),
        tasks=tasks,
        headers=headers,
        timeout=pick("timeout", preset.timeout),
        retry_max=pick("retry_max", preset.retry_max),
        retry_delay=pick("retry_delay", preset.retry_delay),
        concurrency=pick("concurrency", preset.concurrency),
        rate_limit=pick("rate_limit", preset.rate_limit),
        dedup_enabled=pick("dedup_enabled", preset.dedup_enabled),
        meta=overrides.get("meta", {}),
    )


def _resolve_forward_refs() -> None:
    from crawler.crawler.task import TaskConfig, TaskResult

    CrawlerConfig.model_rebuild(
        _types_namespace={"TaskConfig": TaskConfig, "TaskResult": TaskResult},
    )
    CrawlerResult.model_rebuild(_types_namespace={"TaskResult": TaskResult})


_resolve_forward_refs()

__all__ = [
    "Crawler",
    "CrawlerBuildOptions",
    "CrawlerConfig",
    "CrawlerContext",
    "CrawlerResult",
    "DownloaderType",
    "DeduplicationStrategy",
    "RateLimiter",
    "UrlDeduplicator",
    "build_crawler_config",
    "task_config_from_line",
]
