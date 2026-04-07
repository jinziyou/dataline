"""DataExtractor：从详情/数据页提取结构化数据。"""

from __future__ import annotations

import pytest

from crawler.crawler.downloaders.base import DownloadResponse
from crawler.crawler.extractor import DataExtractor


def _resp(text: str, url: str = "https://example.test/article/1") -> DownloadResponse:
    return DownloadResponse(
        url=url,
        status_code=200,
        content=text.encode(),
        text=text,
        headers={},
        content_type="text/html",
    )


DETAIL_HTML = """
<html>
<head><title>Page Title</title></head>
<body>
    <h1 class="title">文章标题</h1>
    <span class="publish-date">2025-01-15</span>
    <div class="article-body">
        <p>第一段正文内容。</p>
        <p>第二段正文内容。</p>
    </div>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_extracts_title_with_selector() -> None:
    ext = DataExtractor(title_selector="h1.title")
    items = await ext.extract(
        response=_resp(DETAIL_HTML),
        line_id="l1",
        source_id="s1",
        line_name="Channel",
        task_id="t1",
    )
    assert len(items) == 1
    assert items[0].title == "文章标题"


@pytest.mark.asyncio
async def test_extracts_content_with_selector() -> None:
    ext = DataExtractor(content_selector=".article-body")
    items = await ext.extract(
        response=_resp(DETAIL_HTML),
        line_id="l1",
        source_id="s1",
        task_id="t1",
    )
    assert "第一段正文内容" in items[0].content
    assert "第二段正文内容" in items[0].content


@pytest.mark.asyncio
async def test_extracts_time_to_raw() -> None:
    ext = DataExtractor(time_selector=".publish-date")
    items = await ext.extract(
        response=_resp(DETAIL_HTML),
        line_id="l1",
        source_id="s1",
        task_id="t1",
    )
    assert items[0].raw["published_at_raw"] == "2025-01-15"


@pytest.mark.asyncio
async def test_fallback_to_line_name_when_title_selector_misses() -> None:
    ext = DataExtractor(title_selector=".nonexistent")
    items = await ext.extract(
        response=_resp(DETAIL_HTML),
        line_id="l1",
        source_id="s1",
        line_name="Fallback Name",
        task_id="t1",
    )
    assert items[0].title == "Fallback Name"


@pytest.mark.asyncio
async def test_fallback_to_full_text_when_content_selector_misses() -> None:
    ext = DataExtractor(content_selector=".nonexistent")
    items = await ext.extract(
        response=_resp(DETAIL_HTML),
        line_id="l1",
        source_id="s1",
        task_id="t1",
    )
    assert items[0].content == DETAIL_HTML


@pytest.mark.asyncio
async def test_no_selectors_returns_full_page() -> None:
    ext = DataExtractor()
    items = await ext.extract(
        response=_resp(DETAIL_HTML),
        line_id="l1",
        source_id="s1",
        line_name="Chan",
        task_id="t1",
    )
    assert len(items) == 1
    assert items[0].title == "Chan"
    assert items[0].content == DETAIL_HTML


@pytest.mark.asyncio
async def test_all_selectors_together() -> None:
    ext = DataExtractor(
        title_selector="h1.title",
        time_selector=".publish-date",
        content_selector=".article-body",
    )
    items = await ext.extract(
        response=_resp(DETAIL_HTML),
        line_id="l1",
        source_id="s1",
        task_id="t1",
    )
    item = items[0]
    assert item.title == "文章标题"
    assert item.raw["published_at_raw"] == "2025-01-15"
    assert "第一段正文内容" in item.content
    assert item.url == "https://example.test/article/1"
    assert item.line_id == "l1"
    assert item.source_id == "s1"


@pytest.mark.asyncio
async def test_empty_html() -> None:
    ext = DataExtractor(title_selector="h1", content_selector=".body")
    items = await ext.extract(
        response=_resp(""),
        line_id="l1",
        source_id="s1",
        line_name="X",
        task_id="t1",
    )
    assert len(items) == 1
    assert items[0].title == "X"
    assert items[0].content == ""
