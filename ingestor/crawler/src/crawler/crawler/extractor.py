"""
提取器层级：Extractor（协议）→ LinkExtractor / DataExtractor / PageExtractor

- LinkExtractor：从列表/导航页提取下一级 URL（一个 Task 可有多个，多级导航时串联）
- DataExtractor：从数据/详情页提取结构化数据（标题、时间、正文）
- PageExtractor：默认整页提取器（向后兼容，无选择器时直接包装整页为 Data）
"""

from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.crawler.data import Data
from crawler.crawler.downloaders.base import DownloadResponse


@runtime_checkable
class Extractor(Protocol):
    """从单次下载结果中提取 Data 列表（数据提取器统一接口）"""

    async def extract(
        self,
        *,
        response: DownloadResponse,
        line_id: str,
        source_id: str,
        line_name: str,
        task_id: str,
    ) -> list[Data]: ...


class LinkExtractor:
    """
    链接提取器：从列表/导航页中提取下一级 URL。

    对应 Task 执行管线中的链接发现层；每个 Task 可配置一个或多个
    LinkExtractor（多级导航时按顺序串联）。
    """

    def __init__(self, selector: str = "a[href]") -> None:
        self.selector = selector

    async def extract_links(
        self,
        response: DownloadResponse,
        *,
        base_url: str | None = None,
    ) -> list[str]:
        """解析 HTML 并返回去重后的绝对 URL 列表。"""
        soup = BeautifulSoup(response.text, "html.parser")
        base = base_url or response.url
        seen: set[str] = set()
        urls: list[str] = []
        for tag in soup.select(self.selector):
            href = tag.get("href")
            if not href or not isinstance(href, str):
                continue
            href = href.strip()
            if not href or href.startswith(("#", "javascript:")):
                continue
            absolute = urljoin(base, href) if base else href
            if absolute not in seen:
                seen.add(absolute)
                urls.append(absolute)
        return urls


class DataExtractor:
    """
    数据提取器：从详情/数据页中提取结构化内容（标题、时间、正文）。

    对应 Task 执行管线中的数据抽取层；选择器为 CSS 选择器字符串。
    """

    def __init__(
        self,
        *,
        title_selector: str | None = None,
        time_selector: str | None = None,
        content_selector: str | None = None,
    ) -> None:
        self.title_selector = title_selector
        self.time_selector = time_selector
        self.content_selector = content_selector

    async def extract(
        self,
        *,
        response: DownloadResponse,
        line_id: str,
        source_id: str,
        line_name: str = "",
        task_id: str = "",
    ) -> list[Data]:
        soup = BeautifulSoup(response.text, "html.parser")

        title = self._extract_text(soup, self.title_selector) or line_name
        time_text = self._extract_text(soup, self.time_selector)
        content = self._extract_text(soup, self.content_selector) or response.text

        raw: dict = {"status_code": response.status_code}
        if time_text:
            raw["published_at_raw"] = time_text

        item = Data(
            id=uuid.uuid4().hex[:12],
            line_id=line_id,
            source_id=source_id,
            url=response.url,
            title=title,
            content=content,
            content_type=response.content_type,
            raw=raw,
        )
        return [item]

    @staticmethod
    def _extract_text(soup: BeautifulSoup, selector: str | None) -> str | None:
        if not selector:
            return None
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None


class PageExtractor:
    """
    默认提取器：将整页作为单条 Data。

    适合「Line URL 即资源页」的场景；导航页需链接抽取时可换用 LinkExtractor + DataExtractor 管线。
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
