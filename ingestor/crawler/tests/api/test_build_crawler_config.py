"""API：build_crawler_config / generate_crawler_config。"""

from __future__ import annotations

from crawler.crawler import build_crawler_config
from crawler.source import Line, Source, SourceType, generate_crawler_config


def test_maps_enabled_lines_to_tasks_from_source_lines() -> None:
    source = Source(
        id="s1",
        name="API",
        type=SourceType.API,
        lines=[
            Line(id="l1", source_id="s1", name="users", url="https://api.test/users"),
            Line(id="l2", source_id="s1", name="posts", url="https://api.test/posts"),
        ],
    )
    cfg = build_crawler_config(source)

    assert cfg.source_id == "s1"
    assert cfg.source_name == "API"
    assert len(cfg.tasks) == 2
    assert {t.line_id for t in cfg.tasks} == {"l1", "l2"}
    assert cfg.tasks[0].params == {}


def test_explicit_lines_override_source_lines() -> None:
    source = Source(
        id="s1",
        name="X",
        type=SourceType.API,
        lines=[Line(id="ignored", source_id="s1", name="i", url="https://i.test")],
    )
    only = [Line(id="l1", source_id="s1", name="u", url="https://only.test")]
    cfg = build_crawler_config(source, only)
    assert len(cfg.tasks) == 1
    assert cfg.tasks[0].line_id == "l1"


def test_line_meta_becomes_task_params() -> None:
    source = Source(
        id="s1",
        name="X",
        type=SourceType.API,
        lines=[
            Line(
                id="l1",
                source_id="s1",
                name="x",
                url="https://x.test",
                meta={"page": 1},
            )
        ],
    )
    cfg = build_crawler_config(source)
    assert cfg.tasks[0].params == {"page": 1}


def test_lines_source_id_normalized_to_source() -> None:
    source = Source(
        id="s1",
        name="X",
        type=SourceType.API,
        lines=[Line(id="l1", source_id="wrong", name="x", url="https://x.test")],
    )
    assert source.lines[0].source_id == "s1"


def test_generate_crawler_config_compat() -> None:
    source = Source(
        id="s1",
        name="A",
        type=SourceType.API,
        lines=[Line(id="l1", source_id="s1", name="u", url="https://a.test")],
    )
    cfg = generate_crawler_config(source)
    assert cfg.source_id == "s1"
    assert len(cfg.tasks) == 1
