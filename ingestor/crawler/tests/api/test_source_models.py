"""API 类型 Source 行为。"""

from __future__ import annotations

from crawler.source import Source, SourceType


def test_source_without_lines_and_no_source_url() -> None:
    s = Source(id="s1", name="Site", type=SourceType.API)
    assert len(s.lines) == 1
    assert s.lines[0].url is None
