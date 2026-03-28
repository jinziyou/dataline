"""Line 模型（与 SourceType 无关）。"""

from __future__ import annotations

from crawler.source import Line


def test_line_belongs_to_source() -> None:
    line = Line(id="l1", source_id="s1", name="feed", url="https://example.test/feed")
    assert line.source_id == "s1"
