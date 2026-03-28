"""TaskExecutor：最小执行单元。"""

from __future__ import annotations

import pytest

from crawler.crawler import (
    CrawlerConfig,
    CrawlerContext,
    TaskConfig,
    TaskExecutor,
    TaskStatus,
)
from crawler.crawler.data import Data

from tests.stubs import StubDownloader


@pytest.mark.asyncio
async def test_execute_without_url_returns_success_and_empty_items(stub_downloader: StubDownloader) -> None:
    cfg = CrawlerConfig(
        crawler_id="c1",
        source_id="s1",
        tasks=[TaskConfig(task_id="t1", line_id="l1")],
    )
    async with CrawlerContext(cfg, downloader=stub_downloader) as ctx:
        ex = TaskExecutor(TaskConfig(task_id="t1", line_id="l1"), ctx)
        result = await ex.execute()
    assert result.status == TaskStatus.SUCCESS
    assert result.items == []


@pytest.mark.asyncio
async def test_execute_downloads_and_extracts(
    minimal_crawler_config: CrawlerConfig,
    stub_downloader: StubDownloader,
) -> None:
    async with CrawlerContext(minimal_crawler_config, downloader=stub_downloader) as ctx:
        ex = TaskExecutor(minimal_crawler_config.tasks[0], ctx)
        result = await ex.execute()
    assert result.status == TaskStatus.SUCCESS
    assert len(result.items) == 1
    assert result.items[0].url == "https://example.test/a"
    assert stub_downloader.urls == ["https://example.test/a"]


@pytest.mark.asyncio
async def test_max_items_truncates(
    minimal_crawler_config: CrawlerConfig,
    stub_downloader: StubDownloader,
) -> None:
    class MultiExtractor:
        async def extract(self, *, response, line_id, source_id, line_name, task_id):
            _ = response, line_name, task_id
            return [
                Data(
                    id=f"id{i}",
                    line_id=line_id,
                    source_id=source_id,
                    url=f"https://x.test/{i}",
                    title="t",
                    content="c",
                )
                for i in range(5)
            ]

    task = minimal_crawler_config.tasks[0].model_copy(update={"max_items": 2})
    async with CrawlerContext(minimal_crawler_config, downloader=stub_downloader) as ctx:
        ex = TaskExecutor(task, ctx, extractor=MultiExtractor())
        result = await ex.execute()
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_execute_marks_failed_on_downloader_error(
    minimal_crawler_config: CrawlerConfig,
) -> None:
    class BoomDownloader(StubDownloader):
        async def download(self, url, **kwargs):
            raise RuntimeError("network down")

    async with CrawlerContext(minimal_crawler_config, downloader=BoomDownloader()) as ctx:
        ex = TaskExecutor(minimal_crawler_config.tasks[0], ctx)
        result = await ex.execute()
    assert result.status == TaskStatus.FAILED
    assert "network down" in (result.error or "")
