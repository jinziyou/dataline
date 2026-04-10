"""共享 fixtures。"""

from __future__ import annotations

import pytest

from crawler.crawler import CrawlerConfig, DownloaderType, TaskConfig

from tests.stubs import StubDownloader


@pytest.fixture
def stub_downloader() -> StubDownloader:
    return StubDownloader()


@pytest.fixture
def minimal_crawler_config() -> CrawlerConfig:
    return CrawlerConfig(
        crawler_id="c-test",
        source_id="s-test",
        source_name="Test Source",
        downloader=DownloaderType.HTTP,
        tasks=[
            TaskConfig(task_id="t-1", line_id="l-1", line_name="L1", url="https://example.test/a"),
        ],
        retry_max=0,  # 单元测试中禁用重试，避免测试变慢
    )
