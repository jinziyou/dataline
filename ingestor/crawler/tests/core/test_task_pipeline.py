"""TaskExecutor 多级链接提取管线测试。"""

from __future__ import annotations

import pytest

from crawler.crawler import (
    CrawlerConfig,
    CrawlerContext,
    TaskConfig,
    TaskExecutor,
    TaskStatus,
)
from crawler.crawler.extractor import DataExtractor, LinkExtractor
from crawler.crawler.task import ExtractorConfig

from tests.stubs import MappedStubDownloader

LISTING_HTML = """
<ul class="news">
    <li><a href="https://site.test/article/1">Article 1</a></li>
    <li><a href="https://site.test/article/2">Article 2</a></li>
    <li><a href="https://site.test/article/3">Article 3</a></li>
</ul>
"""

ARTICLE_1 = """
<h1 class="title">Title One</h1>
<span class="date">2025-01-01</span>
<div class="body"><p>Content of article one.</p></div>
"""

ARTICLE_2 = """
<h1 class="title">Title Two</h1>
<span class="date">2025-01-02</span>
<div class="body"><p>Content of article two.</p></div>
"""

ARTICLE_3 = """
<h1 class="title">Title Three</h1>
<span class="date">2025-01-03</span>
<div class="body"><p>Content of article three.</p></div>
"""


def _make_config(
    url: str = "https://site.test/news",
    *,
    link_selectors: list[str] | None = None,
    title_sel: str | None = None,
    time_sel: str | None = None,
    content_sel: str | None = None,
    max_items: int | None = None,
) -> tuple[CrawlerConfig, TaskConfig]:
    extractors = ExtractorConfig(
        link_selectors=link_selectors or [],
        title_selector=title_sel,
        time_selector=time_sel,
        content_selector=content_sel,
    )
    task = TaskConfig(
        task_id="t1",
        line_id="l1",
        line_name="News",
        url=url,
        max_items=max_items,
        extractors=extractors,
    )
    crawler_cfg = CrawlerConfig(
        crawler_id="c1",
        source_id="s1",
        tasks=[task],
        rate_limit=None,
    )
    return crawler_cfg, task


@pytest.mark.asyncio
async def test_single_link_extractor_pipeline() -> None:
    """列表页 → 链接发现 → 逐个详情页提取数据。"""
    stub = MappedStubDownloader({
        "https://site.test/news": LISTING_HTML,
        "https://site.test/article/1": ARTICLE_1,
        "https://site.test/article/2": ARTICLE_2,
        "https://site.test/article/3": ARTICLE_3,
    })
    crawler_cfg, task = _make_config(
        link_selectors=[".news a"],
        title_sel="h1.title",
        content_sel=".body",
    )
    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 3
    titles = {item.title for item in result.items}
    assert titles == {"Title One", "Title Two", "Title Three"}


@pytest.mark.asyncio
async def test_pipeline_with_max_items() -> None:
    """管线中 max_items 限制最终产出条数。"""
    stub = MappedStubDownloader({
        "https://site.test/news": LISTING_HTML,
        "https://site.test/article/1": ARTICLE_1,
        "https://site.test/article/2": ARTICLE_2,
        "https://site.test/article/3": ARTICLE_3,
    })
    crawler_cfg, task = _make_config(
        link_selectors=[".news a"],
        title_sel="h1.title",
        max_items=2,
    )
    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_pipeline_dedup_skips_duplicate_urls() -> None:
    """管线中去重避免重复抓取同一详情页。"""
    listing = """
    <a href="https://site.test/article/1">A</a>
    <a href="https://site.test/article/1">A dup</a>
    <a href="https://site.test/article/2">B</a>
    """
    stub = MappedStubDownloader({
        "https://site.test/news": listing,
        "https://site.test/article/1": ARTICLE_1,
        "https://site.test/article/2": ARTICLE_2,
    })
    crawler_cfg, task = _make_config(link_selectors=["a"])
    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_multilevel_link_extractors() -> None:
    """多级链接提取：分类页 → 列表页 → 详情页。"""
    category_html = """
    <div class="cat">
        <a href="https://site.test/cat/tech">Tech</a>
        <a href="https://site.test/cat/science">Science</a>
    </div>
    """
    tech_html = '<a href="https://site.test/article/1" class="item">A1</a>'
    science_html = '<a href="https://site.test/article/2" class="item">A2</a>'

    stub = MappedStubDownloader({
        "https://site.test/": category_html,
        "https://site.test/cat/tech": tech_html,
        "https://site.test/cat/science": science_html,
        "https://site.test/article/1": ARTICLE_1,
        "https://site.test/article/2": ARTICLE_2,
    })
    crawler_cfg, task = _make_config(
        url="https://site.test/",
        link_selectors=[".cat a", "a.item"],
        title_sel="h1.title",
    )
    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 2
    titles = {item.title for item in result.items}
    assert "Title One" in titles
    assert "Title Two" in titles


@pytest.mark.asyncio
async def test_empty_link_results_produce_no_data() -> None:
    """列表页无匹配链接时返回空数据。"""
    stub = MappedStubDownloader({
        "https://site.test/news": "<p>No links</p>",
    })
    crawler_cfg, task = _make_config(link_selectors=[".nonexistent a"])
    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert result.items == []


@pytest.mark.asyncio
async def test_no_link_extractors_uses_direct_mode() -> None:
    """无 link_selectors 时回退到直接提取模式（PageExtractor 行为）。"""
    stub = MappedStubDownloader({
        "https://site.test/page": "<html>Direct content</html>",
    })
    crawler_cfg, task = _make_config(url="https://site.test/page")
    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 1
    assert "Direct content" in result.items[0].content


@pytest.mark.asyncio
async def test_explicit_link_and_data_extractors_injected() -> None:
    """通过构造参数注入 LinkExtractor 和 DataExtractor。"""
    stub = MappedStubDownloader({
        "https://site.test/news": LISTING_HTML,
        "https://site.test/article/1": ARTICLE_1,
        "https://site.test/article/2": ARTICLE_2,
        "https://site.test/article/3": ARTICLE_3,
    })
    crawler_cfg, task = _make_config()
    link_ext = LinkExtractor(selector=".news a")
    data_ext = DataExtractor(title_selector="h1.title", content_selector=".body")

    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(
            task, ctx,
            link_extractors=[link_ext],
            data_extractor=data_ext,
        )
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_pipeline_with_time_extraction() -> None:
    """管线提取时间信息。"""
    stub = MappedStubDownloader({
        "https://site.test/news": '<a href="https://site.test/article/1">A</a>',
        "https://site.test/article/1": ARTICLE_1,
    })
    crawler_cfg, task = _make_config(
        link_selectors=["a"],
        title_sel="h1.title",
        time_sel=".date",
        content_sel=".body",
    )
    async with CrawlerContext(crawler_cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert len(result.items) == 1
    assert result.items[0].raw.get("published_at_raw") == "2025-01-01"
