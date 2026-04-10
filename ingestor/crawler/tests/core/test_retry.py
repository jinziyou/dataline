"""TaskExecutor：下载重试与 HTTP 错误处理。"""

from __future__ import annotations

import pytest

from crawler.crawler import (
    CrawlerConfig,
    CrawlerContext,
    TaskConfig,
    TaskExecutor,
    TaskStatus,
)
from crawler.crawler.downloaders.base import BaseDownloader, DownloadResponse
from crawler.crawler.task import DownloadError

from tests.stubs import StubDownloader


def _ok_response(url: str = "https://example.test/a") -> DownloadResponse:
    return DownloadResponse(
        url=url,
        status_code=200,
        content=b"<html>ok</html>",
        text="<html>ok</html>",
        headers={},
        content_type="text/html",
    )


def _error_response(url: str, status: int) -> DownloadResponse:
    return DownloadResponse(
        url=url,
        status_code=status,
        content=b"",
        text="",
        headers={},
        content_type="text/html",
    )


class SequenceStubDownloader(BaseDownloader):
    """按调用顺序依次返回预设响应或抛出预设异常。"""

    def __init__(self, responses: list[DownloadResponse | Exception]) -> None:
        self._queue = list(responses)
        self.call_count = 0

    async def download(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> DownloadResponse:
        self.call_count += 1
        if not self._queue:
            return _ok_response(url)
        resp = self._queue.pop(0)
        if isinstance(resp, Exception):
            raise resp
        resp.url = url
        return resp

    async def close(self) -> None:
        pass


def _make_config(
    retry_max: int = 3,
    retry_delay: float = 0,
    url: str = "https://example.test/a",
) -> tuple[CrawlerConfig, TaskConfig]:
    task = TaskConfig(task_id="t1", line_id="l1", url=url)
    cfg = CrawlerConfig(
        crawler_id="c1",
        source_id="s1",
        tasks=[task],
        retry_max=retry_max,
        retry_delay=retry_delay,
        rate_limit=None,
    )
    return cfg, task


# ---------------------------------------------------------------------------
# 5xx：应重试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt() -> None:
    """第一次 500，第二次 200 → 任务成功。"""
    url = "https://example.test/a"
    stub = SequenceStubDownloader([
        _error_response(url, 500),
        _ok_response(url),
    ])
    cfg, task = _make_config(retry_max=2)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        ex = TaskExecutor(task, ctx)
        result = await ex.execute()

    assert result.status == TaskStatus.SUCCESS
    assert stub.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_on_repeated_5xx() -> None:
    """持续 500 → 达到 retry_max 后任务失败。"""
    url = "https://example.test/a"
    stub = SequenceStubDownloader([
        _error_response(url, 500),
        _error_response(url, 500),
        _error_response(url, 500),
        _error_response(url, 500),
    ])
    cfg, task = _make_config(retry_max=3)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        ex = TaskExecutor(task, ctx)
        result = await ex.execute()

    assert result.status == TaskStatus.FAILED
    assert "500" in (result.error or "")
    assert stub.call_count == 4  # 首次 + 3 次重试


@pytest.mark.asyncio
async def test_retry_on_network_exception() -> None:
    """网络异常后重试，最终成功。"""
    url = "https://example.test/a"
    stub = SequenceStubDownloader([
        ConnectionError("connection refused"),
        _ok_response(url),
    ])
    cfg, task = _make_config(retry_max=2)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        ex = TaskExecutor(task, ctx)
        result = await ex.execute()

    assert result.status == TaskStatus.SUCCESS
    assert stub.call_count == 2


@pytest.mark.asyncio
async def test_network_exception_exhausted_raises_last_error() -> None:
    """网络异常且全部重试耗尽后任务失败，错误信息保留。"""
    url = "https://example.test/a"
    stub = SequenceStubDownloader([
        ConnectionError("timeout"),
        ConnectionError("timeout"),
    ])
    cfg, task = _make_config(retry_max=1)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        ex = TaskExecutor(task, ctx)
        result = await ex.execute()

    assert result.status == TaskStatus.FAILED
    assert "timeout" in (result.error or "")
    assert stub.call_count == 2


# ---------------------------------------------------------------------------
# 4xx：不应重试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_retry_on_4xx() -> None:
    """4xx 客户端错误不重试，直接失败。"""
    url = "https://example.test/a"
    stub = SequenceStubDownloader([
        _error_response(url, 404),
        _ok_response(url),  # 永远不应被调用
    ])
    cfg, task = _make_config(retry_max=3)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        ex = TaskExecutor(task, ctx)
        result = await ex.execute()

    assert result.status == TaskStatus.FAILED
    assert "404" in (result.error or "")
    assert stub.call_count == 1  # 只尝试了一次


@pytest.mark.asyncio
async def test_no_retry_on_403() -> None:
    """403 同样不重试。"""
    url = "https://example.test/a"
    stub = SequenceStubDownloader([_error_response(url, 403)])
    cfg, task = _make_config(retry_max=3)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        ex = TaskExecutor(task, ctx)
        result = await ex.execute()

    assert result.status == TaskStatus.FAILED
    assert stub.call_count == 1


# ---------------------------------------------------------------------------
# retry_max=0：禁用重试
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_max_0_means_no_retry() -> None:
    """retry_max=0 时出错立即失败，不重试。"""
    url = "https://example.test/a"
    stub = SequenceStubDownloader([
        _error_response(url, 503),
        _ok_response(url),
    ])
    cfg, task = _make_config(retry_max=0)
    async with CrawlerContext(cfg, downloader=stub) as ctx:
        ex = TaskExecutor(task, ctx)
        result = await ex.execute()

    assert result.status == TaskStatus.FAILED
    assert stub.call_count == 1


# ---------------------------------------------------------------------------
# DownloadError 异常属性
# ---------------------------------------------------------------------------


def test_download_error_has_status_code() -> None:
    err = DownloadError("HTTP 503: https://x.test/", status_code=503)
    assert err.status_code == 503
    assert "503" in str(err)


def test_download_error_without_status_code() -> None:
    err = DownloadError("connection refused")
    assert err.status_code is None
