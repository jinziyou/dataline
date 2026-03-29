"""Extractor：响应 → Data 列表。"""

from __future__ import annotations

import pytest

from crawler.crawler import PageExtractor
from crawler.crawler.downloaders.base import DownloadResponse


@pytest.mark.asyncio
async def test_page_extractor_wraps_response_as_single_data() -> None:
    ext = PageExtractor()
    resp = DownloadResponse(
        url="https://x.test/doc",
        status_code=200,
        content=b"<p>hi</p>",
        text="<p>hi</p>",
        headers={},
        content_type="text/html",
    )
    items = await ext.extract(
        response=resp,
        line_id="l1",
        source_id="s1",
        line_name="Channel",
        task_id="t1",
    )
    assert len(items) == 1
    assert items[0].line_id == "l1"
    assert items[0].source_id == "s1"
    assert items[0].url == "https://x.test/doc"
    assert items[0].title == "Channel"
    assert items[0].content == "<p>hi</p>"
    assert items[0].raw["status_code"] == 200
