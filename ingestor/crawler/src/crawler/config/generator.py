"""
配置生成器

根据 Source、Line 与预设参数，自动生成 CrawlerConfig 和 TaskConfig。
"""

from __future__ import annotations

import uuid
from typing import Any

from crawler.models.source import Source, Line
from crawler.models.execution import CrawlerConfig, TaskConfig
from crawler.config.presets import get_preset


def _gen_id() -> str:
    return uuid.uuid4().hex[:12]


def generate_crawler_config(
    source: Source,
    lines: list[Line],
    *,
    overrides: dict[str, Any] | None = None,
) -> CrawlerConfig:
    """
    根据 Source 和 Lines 自动生成 CrawlerConfig。

    1. 从预设配置中获取该类型数据源的默认参数
    2. 用 source 元数据补充/覆盖
    3. 用 overrides 进行最终覆盖
    4. 为每个 line 生成对应的 TaskConfig
    """
    preset = get_preset(source.type)
    overrides = overrides or {}

    tasks = [
        TaskConfig(
            task_id=f"task-{_gen_id()}",
            line_id=line.id,
            line_name=line.name,
            url=line.url,
            params=line.meta,
        )
        for line in lines
        if line.enabled
    ]

    return CrawlerConfig(
        crawler_id=f"crawler-{_gen_id()}",
        source_id=source.id,
        source_name=source.name,
        downloader=overrides.get("downloader", preset.downloader),
        tasks=tasks,
        headers={**preset.headers, **overrides.get("headers", {})},
        timeout=overrides.get("timeout", preset.timeout),
        retry_max=overrides.get("retry_max", preset.retry_max),
        retry_delay=overrides.get("retry_delay", preset.retry_delay),
        concurrency=overrides.get("concurrency", preset.concurrency),
        rate_limit=overrides.get("rate_limit", preset.rate_limit),
        dedup_enabled=overrides.get("dedup_enabled", preset.dedup_enabled),
        meta=overrides.get("meta", {}),
    )
