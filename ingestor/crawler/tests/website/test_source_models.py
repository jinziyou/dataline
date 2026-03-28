"""WEBSITE 类型 Source / Line 行为。"""

from __future__ import annotations

from crawler.source import Source, SourceType


def test_source_requires_id_and_name() -> None:
    s = Source(id="s1", name="Site", type=SourceType.WEBSITE)
    assert s.type == SourceType.WEBSITE
    assert s.enabled is True


def test_source_without_lines_gets_default_line_matching_url() -> None:
    s = Source(
        id="s1",
        name="Site",
        type=SourceType.WEBSITE,
        url="https://example.test/root",
    )
    assert len(s.lines) == 1
    assert s.lines[0].id == "s1-default-line"
    assert s.lines[0].source_id == "s1"
    assert s.lines[0].name == "default"
    assert s.lines[0].url == "https://example.test/root"
