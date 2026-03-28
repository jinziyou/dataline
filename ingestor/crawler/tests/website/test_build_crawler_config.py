"""WEBSITE：build_crawler_config（依赖网站类预设）。"""

from __future__ import annotations

from crawler.crawler import CrawlerBuildOptions, DownloaderType, build_crawler_config
from crawler.source import Line, Source, SourceType


def test_skips_disabled_lines() -> None:
    source = Source(
        id="s1",
        name="X",
        type=SourceType.WEBSITE,
        lines=[
            Line(id="l1", source_id="s1", name="on", url="https://a.test", enabled=True),
            Line(id="l2", source_id="s1", name="off", url="https://b.test", enabled=False),
        ],
    )
    cfg = build_crawler_config(source)
    assert len(cfg.tasks) == 1
    assert cfg.tasks[0].line_id == "l1"


def test_overrides_merge_headers_and_timeout() -> None:
    source = Source(
        id="s1",
        name="W",
        type=SourceType.WEBSITE,
        lines=[Line(id="l1", source_id="s1", name="p", url="https://w.test/p")],
    )
    cfg = build_crawler_config(
        source,
        overrides={
            "timeout": 99.0,
            "headers": {"X-Test": "1"},
            "downloader": DownloaderType.PLAYWRIGHT,
        },
    )
    assert cfg.timeout == 99.0
    assert cfg.headers.get("X-Test") == "1"
    assert cfg.downloader == DownloaderType.PLAYWRIGHT


def test_crawler_build_options_override_preset() -> None:
    source = Source(
        id="s1",
        name="W",
        type=SourceType.WEBSITE,
        lines=[Line(id="l1", source_id="s1", name="p", url="https://w.test/p")],
    )
    cfg = build_crawler_config(
        source,
        options=CrawlerBuildOptions(timeout=77.0, headers={"X-Custom": "yes"}),
    )
    assert cfg.timeout == 77.0
    assert cfg.headers["X-Custom"] == "yes"


def test_crawl_defaults_on_source_merged_then_options_then_overrides() -> None:
    source = Source(
        id="s1",
        name="W",
        type=SourceType.WEBSITE,
        lines=[Line(id="l1", source_id="s1", name="p", url="https://w.test/p")],
        crawl_defaults={"timeout": 50.0, "headers": {"X-A": "1"}},
    )
    cfg = build_crawler_config(
        source,
        options=CrawlerBuildOptions(timeout=60.0, headers={"X-B": "2"}),
        overrides={"timeout": 99.0},
    )
    assert cfg.timeout == 99.0
    assert cfg.headers["X-A"] == "1"
    assert cfg.headers["X-B"] == "2"
