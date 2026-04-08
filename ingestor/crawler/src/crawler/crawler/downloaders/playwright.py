"""
Playwright 下载器

基于 Playwright 的异步浏览器下载器实现，支持 JavaScript 渲染的 SPA 页面采集。
浏览器实例在首次下载时惰性启动，多次下载复用同一浏览器上下文。
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from crawler.crawler.downloaders.base import BaseDownloader, DownloadResponse

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright
    from playwright.async_api._context_manager import PlaywrightContextManager

logger = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _require_playwright():
    """延迟导入 playwright，未安装时给出明确提示。"""
    try:
        from playwright.async_api import async_playwright  # noqa: F811
        return async_playwright
    except ImportError:
        raise ImportError(
            "playwright is required for PlaywrightDownloader. "
            "Install it with: uv sync --group browser && uv run playwright install chromium"
        ) from None


class PlaywrightDownloader(BaseDownloader):
    """
    基于 Playwright 的浏览器下载器。

    适用于 JavaScript 渲染的 SPA 页面（如 36kr.com）。每次 download 创建一个新页面（tab），
    等待页面加载并完成 JS 渲染后提取 HTML 内容。

    参数:
        default_headers: 附加到每个请求的公共 HTTP 头
        timeout: 页面导航超时（秒），默认 30s
        wait_until: 页面加载等待策略，可选值：
            - "load"：等待 load 事件
            - "domcontentloaded"：等待 DOMContentLoaded 事件
            - "networkidle"：等待网络空闲（推荐用于 SPA）
            - "commit"：等待收到响应
        headless: 是否使用无头模式，默认 True
        wait_after: 导航完成后额外等待的秒数，让 SPA 完成客户端渲染，默认 0
    """

    def __init__(
        self,
        *,
        default_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        wait_until: str = "networkidle",
        headless: bool = True,
        wait_after: float = 0,
    ) -> None:
        self._default_headers = default_headers or {}
        self._timeout_ms = timeout * 1000
        self._wait_until = wait_until
        self._headless = headless
        self._wait_after = wait_after

        self._pw_cm: PlaywrightContextManager | None = None
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def _ensure_browser(self) -> BrowserContext:
        """惰性启动浏览器，返回共享的 BrowserContext。"""
        if self._context is not None:
            return self._context

        async_playwright = _require_playwright()
        self._pw_cm = async_playwright()
        self._pw = await self._pw_cm.__aenter__()
        self._browser = await self._pw.chromium.launch(headless=self._headless)

        ua = self._default_headers.get("User-Agent", _DEFAULT_USER_AGENT)
        extra = {k: v for k, v in self._default_headers.items() if k != "User-Agent"}

        self._context = await self._browser.new_context(
            user_agent=ua,
            extra_http_headers=extra if extra else None,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        logger.info("Playwright browser launched (headless=%s)", self._headless)
        return self._context

    async def download(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> DownloadResponse:
        context = await self._ensure_browser()
        page = await context.new_page()

        if headers:
            await page.set_extra_http_headers(headers)

        timeout_ms = timeout * 1000
        try:
            response = await page.goto(
                url,
                wait_until=self._wait_until,
                timeout=timeout_ms,
            )

            await self._wait_for_render(page, timeout_ms)

            if self._wait_after > 0:
                await asyncio.sleep(self._wait_after)

            rendered_html = await page.content()
            status_code = response.status if response else 200
            resp_headers = response.all_headers() if response else {}
            if isinstance(resp_headers, dict):
                resp_headers_dict = resp_headers
            else:
                resp_headers_dict = await resp_headers
            content_type = resp_headers_dict.get("content-type", "text/html")

            logger.debug(
                "Playwright downloaded %s: %d chars, status %d",
                url, len(rendered_html), status_code,
            )

            return DownloadResponse(
                url=page.url,
                status_code=status_code,
                content=rendered_html.encode("utf-8"),
                text=rendered_html,
                headers=resp_headers_dict,
                content_type=content_type,
            )
        finally:
            await page.close()

    async def _wait_for_render(self, page, timeout_ms: float) -> None:
        """
        等待 SPA 完成客户端渲染。

        策略：先等 body 出现子元素，再通过轮询 body 的 innerText 长度确认内容已渲染。
        若 body 文本稳定在 >200 字符且连续两次采样不变，视为渲染完成。
        """
        deadline_ms = min(timeout_ms / 2, 15000)
        try:
            await page.wait_for_function(
                "document.body && document.body.children.length > 0",
                timeout=deadline_ms,
            )
        except Exception:
            return

        poll_interval = 0.5
        max_polls = int(deadline_ms / 1000 / poll_interval)
        prev_len = 0
        stable_count = 0
        for _ in range(max_polls):
            await asyncio.sleep(poll_interval)
            try:
                cur_len = await page.evaluate("document.body.innerText.length")
            except Exception:
                break
            if cur_len > 200 and cur_len == prev_len:
                stable_count += 1
                if stable_count >= 2:
                    break
            else:
                stable_count = 0
            prev_len = cur_len

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._pw_cm is not None:
            await self._pw_cm.__aexit__(None, None, None)
            self._pw_cm = None
            self._pw = None
            logger.info("Playwright browser closed")
