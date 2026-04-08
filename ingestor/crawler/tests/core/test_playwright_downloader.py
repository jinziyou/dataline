"""PlaywrightDownloader 单元测试（不依赖真实浏览器）。

通过 monkeypatch 替换 playwright 的 async_playwright 入口，
验证 PlaywrightDownloader 的生命周期管理、download 行为和资源释放。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from crawler.crawler.downloaders.playwright import PlaywrightDownloader


# ---------------------------------------------------------------------------
# Fake playwright objects
# ---------------------------------------------------------------------------

@dataclass
class FakePage:
    url: str = "https://fake.test/"
    _content: str = "<html><body>rendered</body></html>"
    _closed: bool = False
    _extra_headers: dict[str, str] = field(default_factory=dict)

    async def goto(self, url: str, **kwargs: Any) -> "FakeResponse":
        self.url = url
        return FakeResponse(url=url, status=200)

    async def content(self) -> str:
        return self._content

    async def set_extra_http_headers(self, headers: dict[str, str]) -> None:
        self._extra_headers = headers

    async def close(self) -> None:
        self._closed = True


@dataclass
class FakeResponse:
    url: str = "https://fake.test/"
    status: int = 200

    def all_headers(self) -> dict[str, str]:
        return {"content-type": "text/html; charset=utf-8"}


@dataclass
class FakeContext:
    pages: list[FakePage] = field(default_factory=list)
    _closed: bool = False

    async def new_page(self) -> FakePage:
        page = FakePage()
        self.pages.append(page)
        return page

    async def close(self) -> None:
        self._closed = True


@dataclass
class FakeBrowser:
    contexts: list[FakeContext] = field(default_factory=list)
    _closed: bool = False

    async def new_context(self, **kwargs: Any) -> FakeContext:
        ctx = FakeContext()
        self.contexts.append(ctx)
        return ctx

    async def close(self) -> None:
        self._closed = True


class FakePlaywright:
    """模拟 async_playwright 上下文管理器返回的对象。"""

    def __init__(self) -> None:
        self.browser = FakeBrowser()
        self.chromium = self

    async def launch(self, **kwargs: Any) -> FakeBrowser:
        return self.browser

    async def __aenter__(self) -> "FakePlaywright":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


class FakePlaywrightContextManager:
    """模拟 async_playwright() 返回的上下文管理器。"""

    def __init__(self, pw: FakePlaywright) -> None:
        self.pw = pw

    async def __aenter__(self) -> FakePlaywright:
        return self.pw

    async def __aexit__(self, *args: object) -> None:
        pass


class FakeAsyncPlaywright:
    """模拟 async_playwright 工厂函数。"""

    def __init__(self) -> None:
        self.instance = FakePlaywright()

    def __call__(self) -> FakePlaywrightContextManager:
        return FakePlaywrightContextManager(self.instance)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_pw(monkeypatch: pytest.MonkeyPatch) -> FakeAsyncPlaywright:
    """Patch _require_playwright 返回 fake async_playwright。"""
    fake = FakeAsyncPlaywright()
    monkeypatch.setattr(
        "crawler.crawler.downloaders.playwright._require_playwright",
        lambda: fake,
    )
    return fake


@pytest.mark.asyncio
async def test_download_returns_rendered_html(fake_pw: FakeAsyncPlaywright) -> None:
    dl = PlaywrightDownloader()
    resp = await dl.download("https://example.test/spa")
    assert resp.status_code == 200
    assert "rendered" in resp.text
    assert resp.url == "https://example.test/spa"
    assert resp.content_type == "text/html; charset=utf-8"
    await dl.close()


@pytest.mark.asyncio
async def test_browser_launched_lazily(fake_pw: FakeAsyncPlaywright) -> None:
    dl = PlaywrightDownloader()
    assert dl._browser is None
    await dl.download("https://example.test/1")
    assert dl._browser is not None
    await dl.close()


@pytest.mark.asyncio
async def test_multiple_downloads_reuse_browser(fake_pw: FakeAsyncPlaywright) -> None:
    dl = PlaywrightDownloader()
    await dl.download("https://example.test/a")
    await dl.download("https://example.test/b")
    browser = fake_pw.instance.browser
    assert len(browser.contexts) == 1
    ctx = browser.contexts[0]
    assert len(ctx.pages) == 2
    assert all(p._closed for p in ctx.pages)
    await dl.close()


@pytest.mark.asyncio
async def test_close_releases_resources(fake_pw: FakeAsyncPlaywright) -> None:
    dl = PlaywrightDownloader()
    await dl.download("https://example.test/")
    browser = fake_pw.instance.browser
    ctx = browser.contexts[0]
    await dl.close()
    assert ctx._closed
    assert browser._closed
    assert dl._browser is None
    assert dl._context is None
    assert dl._pw is None


@pytest.mark.asyncio
async def test_close_idempotent_before_launch(fake_pw: FakeAsyncPlaywright) -> None:
    dl = PlaywrightDownloader()
    await dl.close()
    assert dl._browser is None


@pytest.mark.asyncio
async def test_extra_headers_forwarded(fake_pw: FakeAsyncPlaywright) -> None:
    dl = PlaywrightDownloader()
    await dl.download("https://example.test/", headers={"X-Custom": "val"})
    browser = fake_pw.instance.browser
    page = browser.contexts[0].pages[0]
    assert page._extra_headers == {"X-Custom": "val"}
    await dl.close()


@pytest.mark.asyncio
async def test_context_manager_protocol(fake_pw: FakeAsyncPlaywright) -> None:
    async with PlaywrightDownloader() as dl:
        resp = await dl.download("https://example.test/ctx")
        assert resp.status_code == 200
    assert dl._browser is None


@pytest.mark.asyncio
async def test_crawler_context_creates_playwright_downloader(
    monkeypatch: pytest.MonkeyPatch,
    fake_pw: FakeAsyncPlaywright,
) -> None:
    """CrawlerContext 在 downloader=PLAYWRIGHT 时自动创建 PlaywrightDownloader。"""
    from crawler.crawler import CrawlerConfig, CrawlerContext, DownloaderType

    config = CrawlerConfig(
        crawler_id="c-pw",
        source_id="s-pw",
        downloader=DownloaderType.PLAYWRIGHT,
    )
    ctx = CrawlerContext(config)
    assert isinstance(ctx.downloader, PlaywrightDownloader)
    await ctx.close()
