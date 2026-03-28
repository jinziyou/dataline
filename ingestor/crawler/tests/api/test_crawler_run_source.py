"""API：Crawler.run_source。"""

from __future__ import annotations

import pytest

from crawler.crawler import Crawler
from crawler.source import Line, Source, SourceType

from tests.stubs import StubDownloader


@pytest.mark.asyncio
async def test_run_source_is_primary_entry_with_stub() -> None:
    stub = StubDownloader(text="<html>ok</html>")
    source = Source(
        id="s1",
        name="T",
        type=SourceType.API,
        lines=[Line(id="l1", source_id="s1", name="a", url="https://a.test/x")],
    )
    result = await Crawler.run_source(source, downloader=stub)
    assert result.source_id == "s1"
    assert result.total_items == 1
    assert stub.urls == ["https://a.test/x"]
