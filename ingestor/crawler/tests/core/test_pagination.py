"""TaskExecutor：自动翻页（next_page_selector / max_pages）。"""

from __future__ import annotations

import pytest

from crawler.crawler import (
    CrawlerConfig,
    CrawlerContext,
    TaskConfig,
    TaskExecutor,
    TaskStatus,
)
from crawler.crawler.task import ExtractorConfig

from tests.stubs import MappedStubDownloader

# ---------------------------------------------------------------------------
# 测试页面 HTML
# ---------------------------------------------------------------------------

PAGE_1 = """
<html><body>
<ul class="list">
    <li><a href="https://site.test/article/1">Article 1</a></li>
    <li><a href="https://site.test/article/2">Article 2</a></li>
</ul>
<a class="next-page" href="https://site.test/news?page=2">下一页</a>
</body></html>
"""

PAGE_2 = """
<html><body>
<ul class="list">
    <li><a href="https://site.test/article/3">Article 3</a></li>
    <li><a href="https://site.test/article/4">Article 4</a></li>
</ul>
<a class="next-page" href="https://site.test/news?page=3">下一页</a>
</body></html>
"""

PAGE_3 = """
<html><body>
<ul class="list">
    <li><a href="https://site.test/article/5">Article 5</a></li>
</ul>
<!-- 末页无下一页链接 -->
</body></html>
"""

ARTICLE_TEMPLATE = """
<html><body>
<h1 class="title">{title}</h1>
<div class="body"><p>Content here.</p></div>
</body></html>
"""


def _article(n: int) -> str:
    return ARTICLE_TEMPLATE.format(title=f"Article {n}")


def _make_config(
    *,
    url: str = "https://site.test/news",
    link_selectors: list[str] | None = None,
    next_page_selector: str | None = None,
    max_pages: int | None = None,
    max_items: int | None = None,
) -> tuple[CrawlerConfig, TaskConfig]:
    extractors = ExtractorConfig(
        link_selectors=link_selectors or [".list a"],
        title_selector="h1.title",
        next_page_selector=next_page_selector,
        max_pages=max_pages,
    )
    task = TaskConfig(
        task_id="t1",
        line_id="l1",
        url=url,
        max_items=max_items,
        extractors=extractors,
    )
    cfg = CrawlerConfig(
        crawler_id="c1",
        source_id="s1",
        tasks=[task],
        retry_max=0,
        rate_limit=None,
    )
    return cfg, task


# ---------------------------------------------------------------------------
# 基本翻页
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_follows_all_pages() -> None:
    """配置 next_page_selector 后自动跟随所有分页，收集到全部链接。"""
    stub = MappedStubDownloader({
        "https://site.test/news": PAGE_1,
        "https://site.test/news?page=2": PAGE_2,
        "https://site.test/news?page=3": PAGE_3,
        **{f"https://site.test/article/{i}": _article(i) for i in range(1, 6)},
    })
    cfg, task = _make_config(next_page_selector="a.next-page")
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 5
    titles = {item.title for item in result.items}
    assert titles == {f"Article {i}" for i in range(1, 6)}


@pytest.mark.asyncio
async def test_no_pagination_without_selector() -> None:
    """未配置 next_page_selector 时只抓取第一页。"""
    stub = MappedStubDownloader({
        "https://site.test/news": PAGE_1,
        **{f"https://site.test/article/{i}": _article(i) for i in range(1, 5)},
    })
    cfg, task = _make_config()  # next_page_selector=None
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 2  # 只有第一页的 2 篇


# ---------------------------------------------------------------------------
# max_pages 限制
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_respects_max_pages() -> None:
    """max_pages=2 时只抓取前两页。"""
    stub = MappedStubDownloader({
        "https://site.test/news": PAGE_1,
        "https://site.test/news?page=2": PAGE_2,
        "https://site.test/news?page=3": PAGE_3,
        **{f"https://site.test/article/{i}": _article(i) for i in range(1, 6)},
    })
    cfg, task = _make_config(next_page_selector="a.next-page", max_pages=2)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 4  # 第1页2篇 + 第2页2篇


@pytest.mark.asyncio
async def test_pagination_max_pages_1_is_single_page() -> None:
    """max_pages=1 等价于不翻页。"""
    stub = MappedStubDownloader({
        "https://site.test/news": PAGE_1,
        **{f"https://site.test/article/{i}": _article(i) for i in range(1, 3)},
    })
    cfg, task = _make_config(next_page_selector="a.next-page", max_pages=1)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 2


# ---------------------------------------------------------------------------
# 防循环
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_stops_on_loop_detection() -> None:
    """下一页链接指向已访问 URL 时停止翻页，不无限循环。"""
    looping_page = """
    <ul class="list">
        <li><a href="https://site.test/article/1">Article 1</a></li>
    </ul>
    <a class="next-page" href="https://site.test/news">再来一次</a>
    """
    stub = MappedStubDownloader({
        "https://site.test/news": looping_page,
        "https://site.test/article/1": _article(1),
    })
    cfg, task = _make_config(next_page_selector="a.next-page")
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 1  # 不重复抓取


# ---------------------------------------------------------------------------
# 末页无下一页链接
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_stops_at_last_page() -> None:
    """末页没有 next_page_selector 匹配元素时翻页自动停止。"""
    last_page = """
    <ul class="list">
        <li><a href="https://site.test/article/3">Article 3</a></li>
    </ul>
    """
    stub = MappedStubDownloader({
        "https://site.test/news": PAGE_1,
        "https://site.test/news?page=2": last_page,
        **{f"https://site.test/article/{i}": _article(i) for i in range(1, 4)},
    })
    cfg, task = _make_config(next_page_selector="a.next-page")
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 3  # 第1页2篇 + 第2页1篇


# ---------------------------------------------------------------------------
# max_items 与翻页联动
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pagination_with_max_items() -> None:
    """翻页收集到的链接受 max_items 约束。"""
    stub = MappedStubDownloader({
        "https://site.test/news": PAGE_1,
        "https://site.test/news?page=2": PAGE_2,
        **{f"https://site.test/article/{i}": _article(i) for i in range(1, 5)},
    })
    cfg, task = _make_config(next_page_selector="a.next-page", max_items=3)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        executor = TaskExecutor(task, ctx)
        result = await executor.execute()

    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 3
