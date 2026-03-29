"""
按 SourceType 的默认采集参数模板（source 领域）

取值与 crawler 领域的 DownloaderType 对齐，此处用字面量类型避免 source 依赖 crawler。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from crawler.source.source import SourceType

CrawlerDownloaderId = Literal["http", "playwright"]


class SourcePreset(BaseModel):
    """数据源类型维度的推荐采集默认值（聚合根 Source 之外的类型级策略）"""

    source_type: SourceType
    downloader: CrawlerDownloaderId = "http"
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: float = 30.0
    retry_max: int = 3
    retry_delay: float = 1.0
    concurrency: int = 5
    rate_limit: float | None = None
    dedup_enabled: bool = True
    description: str = ""


_PRESETS: dict[SourceType, SourcePreset] = {
    SourceType.WEBSITE: SourcePreset(
        source_type=SourceType.WEBSITE,
        downloader="http",
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
        timeout=30.0,
        retry_max=3,
        retry_delay=2.0,
        concurrency=3,
        rate_limit=2.0,
        dedup_enabled=True,
        description="公开网站和网络资源：网页、文档、媒体资源",
    ),
    SourceType.API: SourcePreset(
        source_type=SourceType.API,
        downloader="http",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
        retry_max=3,
        retry_delay=1.0,
        concurrency=10,
        rate_limit=None,
        dedup_enabled=True,
        description="API 接口和订阅服务：RESTful/GraphQL API、RSS/Atom、Webhook",
    ),
    SourceType.FILE: SourcePreset(
        source_type=SourceType.FILE,
        downloader="http",
        headers={},
        timeout=120.0,
        retry_max=2,
        retry_delay=5.0,
        concurrency=3,
        rate_limit=None,
        dedup_enabled=True,
        description="文件和存储系统：本地或远程文件、对象存储、FTP",
    ),
    SourceType.STREAM: SourcePreset(
        source_type=SourceType.STREAM,
        downloader="http",
        headers={},
        timeout=0,
        retry_max=5,
        retry_delay=3.0,
        concurrency=1,
        rate_limit=None,
        dedup_enabled=True,
        description="消息与流数据：消息队列、实时流、WebSocket",
    ),
    SourceType.EXTERNAL: SourcePreset(
        source_type=SourceType.EXTERNAL,
        downloader="http",
        headers={},
        timeout=60.0,
        retry_max=3,
        retry_delay=2.0,
        concurrency=5,
        rate_limit=None,
        dedup_enabled=True,
        description="外部结构和第三方系统：数据库、SaaS 平台、遗留系统",
    ),
}


def get_preset(source_type: SourceType) -> SourcePreset:
    return _PRESETS[source_type]


def list_presets() -> dict[SourceType, SourcePreset]:
    return dict(_PRESETS)
