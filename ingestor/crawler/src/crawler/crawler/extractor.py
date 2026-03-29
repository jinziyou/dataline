"""
提取器：将下载响应解析为多条 Data

扩展点：分页、链接发现、结构化解析等可在自定义 Extractor 中实现。
"""

from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from crawler.crawler.data import Data
from crawler.crawler.downloaders.base import DownloadResponse


@runtime_checkable
class Extractor(Protocol):
    """从单次下载结果中提取 Data 列表"""

    async def extract(
        self,
        *,
        response: DownloadResponse,
        line_id: str,
        source_id: str,
        line_name: str,
        task_id: str,
    ) -> list[Data]:
        """根据响应与任务上下文产出数据条目"""
        ...


class PageExtractor:
    """
    默认提取器：将整页作为单条 Data。

    适合「Line URL 即资源页」的场景；导航页需链接抽取时可换用子类或其它 Extractor。
    """

    async def extract(
        self,
        *,
        response: DownloadResponse,
        line_id: str,
        source_id: str,
        line_name: str,
        task_id: str,
    ) -> list[Data]:
        _ = task_id
        item = Data(
            id=uuid.uuid4().hex[:12],
            line_id=line_id,
            source_id=source_id,
            url=response.url,
            title=line_name,
            content=response.text,
            content_type=response.content_type,
            raw={"status_code": response.status_code},
        )
        return [item]
