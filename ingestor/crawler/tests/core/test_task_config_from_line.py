"""task_config_from_line（与 SourceType 无关）。"""

from __future__ import annotations

from crawler.crawler import task_config_from_line
from crawler.source import Line


def test_item_limit_maps_to_task_config() -> None:
    line = Line(
        id="l1",
        source_id="s1",
        name="x",
        url="https://x.test",
        item_limit=3,
    )
    tc = task_config_from_line(line)
    assert tc.max_items == 3
    assert tc.params == {}
