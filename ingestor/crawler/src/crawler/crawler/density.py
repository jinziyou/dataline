"""
信息密度选择器检测器

通过分析页面 HTML 结构，自动推导链接选择器（列表页）和数据选择器（详情页）。
用于从 Source 自动生成 Crawler 配置（ExtractorConfig）。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from bs4 import BeautifulSoup, Tag


@dataclass
class DetectedSelectors:
    """自动检测到的选择器集合"""
    link_selectors: list[str] = field(default_factory=list)
    title_selector: str | None = None
    time_selector: str | None = None
    content_selector: str | None = None


@runtime_checkable
class SelectorDetector(Protocol):
    """选择器检测器协议：从页面内容自动发现 CSS 选择器。"""

    def detect_from_listing(self, html: str) -> list[str]:
        """从列表页检测链接选择器。"""
        ...

    def detect_from_detail(self, html: str) -> DetectedSelectors:
        """从详情页检测数据选择器（标题、时间、内容）。"""
        ...


class DensityBasedDetector:
    """
    基于信息密度的选择器检测器。

    列表页：找到包含最多同类链接的重复容器结构，推导出链接选择器。
    详情页：通过标签语义和文本密度定位标题（h1/h2）、时间（time/.date）、正文（最大文本块）。
    """

    MIN_LINK_GROUP_SIZE = 3

    def detect_from_listing(self, html: str) -> list[str]:
        """分析列表页 HTML，返回链接选择器列表。"""
        soup = BeautifulSoup(html, "html.parser")
        selector = self._find_link_pattern(soup)
        return [selector] if selector else []

    def detect_from_detail(self, html: str) -> DetectedSelectors:
        """分析详情页 HTML，返回标题/时间/正文选择器。"""
        soup = BeautifulSoup(html, "html.parser")
        return DetectedSelectors(
            title_selector=self._detect_title(soup),
            time_selector=self._detect_time(soup),
            content_selector=self._detect_content(soup),
        )

    def _find_link_pattern(self, soup: BeautifulSoup) -> str | None:
        """
        查找链接密度最高的父容器结构。

        算法：将每个 <a href> 标签的父元素签名（tag.class）计数，
        取计数最高且 >= MIN_LINK_GROUP_SIZE 的签名，组合为 CSS 选择器。
        """
        counter: Counter[str] = Counter()
        selector_map: dict[str, str] = {}

        for a_tag in soup.find_all("a", href=True):
            parent = a_tag.parent
            if parent is None or not isinstance(parent, Tag):
                continue
            sig = self._tag_signature(parent)
            counter[sig] += 1
            selector_map.setdefault(sig, f"{sig} a[href]")

        if not counter:
            return None

        best_sig, best_count = counter.most_common(1)[0]
        if best_count < self.MIN_LINK_GROUP_SIZE:
            return None

        return selector_map[best_sig]

    def _detect_title(self, soup: BeautifulSoup) -> str | None:
        for tag_name in ("h1", "h2"):
            tag = soup.find(tag_name)
            if tag and isinstance(tag, Tag) and tag.get_text(strip=True):
                return self._tag_selector(tag)
        return None

    def _detect_time(self, soup: BeautifulSoup) -> str | None:
        time_tag = soup.find("time")
        if time_tag and isinstance(time_tag, Tag):
            return "time"

        for cls in ("date", "time", "publish-date", "pub-date", "datetime", "publish_time"):
            el = soup.find(class_=cls)
            if el and isinstance(el, Tag):
                return f".{cls}"
        return None

    def _detect_content(self, soup: BeautifulSoup) -> str | None:
        for selector in (
            "article",
            ".content",
            ".article-content",
            ".post-content",
            ".article-body",
            "main",
        ):
            el = soup.select_one(selector)
            if el and len(el.get_text(strip=True)) > 100:
                return selector

        best: Tag | None = None
        best_len = 0
        for tag in soup.find_all(["div", "article", "section", "main"]):
            if isinstance(tag, Tag):
                text_len = len(tag.get_text(strip=True))
                if text_len > best_len:
                    best = tag
                    best_len = text_len

        if best and best_len > 100:
            return self._tag_selector(best)
        return None

    @staticmethod
    def _tag_signature(tag: Tag) -> str:
        """生成标签签名：tag_name.class1.class2"""
        name = tag.name
        classes = tag.get("class")
        if classes and isinstance(classes, list):
            return f"{name}.{'.'.join(classes)}"
        return name

    @staticmethod
    def _tag_selector(tag: Tag) -> str:
        """生成单个标签的 CSS 选择器。"""
        classes = tag.get("class")
        if classes and isinstance(classes, list):
            return f"{tag.name}.{'.'.join(classes)}"
        tag_id = tag.get("id")
        if tag_id:
            return f"#{tag_id}"
        return tag.name
