"""Crawler：直接使用 CrawlerConfig 运行（不依赖 Source / SourceType）。"""

from __future__ import annotations

import pytest

from crawler.crawler import Crawler, CrawlerConfig, DownloaderType, TaskConfig, TaskStatus

from tests.stubs import StubDownloader


@pytest.mark.asyncio
async def test_run_executes_all_tasks_with_stub_downloader() -> None:
    stub = StubDownloader(text="<html>x</html>")
    cfg = CrawlerConfig(
        crawler_id="c1",
        source_id="s1",
        downloader=DownloaderType.HTTP,
        tasks=[
            TaskConfig(task_id="t1", line_id="l1", line_name="A", url="https://a.test/1"),
            TaskConfig(task_id="t2", line_id="l2", line_name="B", url="https://b.test/2"),
        ],
    )
    result = await Crawler(cfg, downloader=stub).run()
    assert result.crawler_id == "c1"
    assert result.total_items == 2
    assert result.success_count == 2
    assert result.failed_count == 0
    assert len(stub.urls) == 2


@pytest.mark.asyncio
async def test_dedup_skips_second_task_same_url() -> None:
    stub = StubDownloader()
    url = "https://same.test/page"
    cfg = CrawlerConfig(
        crawler_id="c1",
        source_id="s1",
        tasks=[
            TaskConfig(task_id="t1", line_id="l1", url=url),
            TaskConfig(task_id="t2", line_id="l2", url=url),
        ],
        dedup_enabled=True,
    )
    result = await Crawler(cfg, downloader=stub).run()
    assert result.total_items == 1
    assert stub.urls == [url]


@pytest.mark.asyncio
async def test_crawler_result_counts_failed_task() -> None:
    class Boom(StubDownloader):
        async def download(self, url, **kwargs):
            if "bad" in url:
                raise OSError("boom")
            return await super().download(url, **kwargs)

    cfg = CrawlerConfig(
        crawler_id="c1",
        source_id="s1",
        tasks=[
            TaskConfig(task_id="t1", line_id="l1", url="https://ok.test/"),
            TaskConfig(task_id="t2", line_id="l2", url="https://bad.test/"),
        ],
    )
    result = await Crawler(cfg, downloader=Boom()).run()
    assert result.success_count == 1
    assert result.failed_count == 1
    assert result.task_results[1].status == TaskStatus.FAILED
