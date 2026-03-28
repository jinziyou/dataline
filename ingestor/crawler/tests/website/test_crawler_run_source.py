"""WEBSITE：Crawler.from_source / run。"""

from __future__ import annotations

import pytest

from crawler.crawler import Crawler
from crawler.source import Line, Source, SourceType


@pytest.mark.asyncio
async def test_from_source_same_config_as_run() -> None:
    source = Source(
        id="s1",
        name="T",
        type=SourceType.WEBSITE,
        lines=[Line(id="l1", source_id="s1", name="x", url="https://x.test/")],
    )
    c = Crawler.from_source(source)
    assert c.config.source_id == "s1"
    assert len(c.config.tasks) == 1
    assert c.config.tasks[0].line_id == "l1"
