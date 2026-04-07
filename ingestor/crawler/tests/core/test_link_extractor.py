"""LinkExtractor：从列表/导航页提取链接。"""

from __future__ import annotations

import pytest

from crawler.crawler.downloaders.base import DownloadResponse
from crawler.crawler.extractor import LinkExtractor


def _resp(text: str, url: str = "https://example.test/list") -> DownloadResponse:
    return DownloadResponse(
        url=url,
        status_code=200,
        content=text.encode(),
        text=text,
        headers={},
        content_type="text/html",
    )


@pytest.mark.asyncio
async def test_default_selector_extracts_all_links() -> None:
    html = """
    <ul>
        <li><a href="/page/1">Page 1</a></li>
        <li><a href="/page/2">Page 2</a></li>
        <li><a href="/page/3">Page 3</a></li>
    </ul>
    """
    ext = LinkExtractor()
    urls = await ext.extract_links(_resp(html))
    assert urls == [
        "https://example.test/page/1",
        "https://example.test/page/2",
        "https://example.test/page/3",
    ]


@pytest.mark.asyncio
async def test_custom_selector_filters_links() -> None:
    html = """
    <nav><a href="/nav">Nav</a></nav>
    <div class="list">
        <a href="/item/1" class="item-link">A</a>
        <a href="/item/2" class="item-link">B</a>
    </div>
    """
    ext = LinkExtractor(selector=".list a.item-link")
    urls = await ext.extract_links(_resp(html))
    assert urls == [
        "https://example.test/item/1",
        "https://example.test/item/2",
    ]


@pytest.mark.asyncio
async def test_relative_urls_resolved_with_base() -> None:
    html = '<a href="detail.html">Link</a>'
    ext = LinkExtractor()
    urls = await ext.extract_links(
        _resp(html, url="https://example.test/news/"),
        base_url="https://example.test/news/",
    )
    assert urls == ["https://example.test/news/detail.html"]


@pytest.mark.asyncio
async def test_absolute_urls_preserved() -> None:
    html = '<a href="https://other.test/page">Link</a>'
    ext = LinkExtractor()
    urls = await ext.extract_links(_resp(html))
    assert urls == ["https://other.test/page"]


@pytest.mark.asyncio
async def test_no_links_returns_empty() -> None:
    html = "<p>No links here</p>"
    ext = LinkExtractor()
    urls = await ext.extract_links(_resp(html))
    assert urls == []


@pytest.mark.asyncio
async def test_duplicate_urls_deduplicated() -> None:
    html = """
    <a href="/same">A</a>
    <a href="/same">B</a>
    <a href="/other">C</a>
    """
    ext = LinkExtractor()
    urls = await ext.extract_links(_resp(html))
    assert urls == [
        "https://example.test/same",
        "https://example.test/other",
    ]


@pytest.mark.asyncio
async def test_javascript_and_fragment_links_skipped() -> None:
    html = """
    <a href="javascript:void(0)">JS</a>
    <a href="#">Fragment</a>
    <a href="/real">Real</a>
    """
    ext = LinkExtractor()
    urls = await ext.extract_links(_resp(html))
    assert urls == ["https://example.test/real"]


@pytest.mark.asyncio
async def test_malformed_html_handled_gracefully() -> None:
    html = "<div><a href='/ok'>ok</a><p unclosed"
    ext = LinkExtractor()
    urls = await ext.extract_links(_resp(html))
    assert urls == ["https://example.test/ok"]
