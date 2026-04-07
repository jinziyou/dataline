"""task_config_from_line（与 SourceType 无关）。"""

from __future__ import annotations

from crawler.crawler import EXTRACTOR_CONFIG_META_KEY, task_config_from_line
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


def test_extractor_config_from_line_meta() -> None:
    line = Line(
        id="l1",
        source_id="s1",
        name="news",
        url="https://x.test/news",
        meta={
            EXTRACTOR_CONFIG_META_KEY: {
                "link_selectors": [".list a"],
                "title_selector": "h1",
                "content_selector": ".body",
            },
            "custom_key": "value",
        },
    )
    tc = task_config_from_line(line)
    assert tc.extractors.link_selectors == [".list a"]
    assert tc.extractors.title_selector == "h1"
    assert tc.extractors.content_selector == ".body"
    assert tc.params == {"custom_key": "value"}
    assert EXTRACTOR_CONFIG_META_KEY not in tc.params


def test_no_extractor_config_meta_gives_defaults() -> None:
    line = Line(
        id="l1",
        source_id="s1",
        name="x",
        url="https://x.test",
        meta={"page": 1},
    )
    tc = task_config_from_line(line)
    assert tc.extractors.link_selectors == []
    assert tc.extractors.has_data_selectors is False
    assert tc.params == {"page": 1}


def test_empty_extractor_config_meta_gives_defaults() -> None:
    line = Line(
        id="l1",
        source_id="s1",
        name="x",
        url="https://x.test",
        meta={EXTRACTOR_CONFIG_META_KEY: {}},
    )
    tc = task_config_from_line(line)
    assert tc.extractors.link_selectors == []
