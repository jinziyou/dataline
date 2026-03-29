from __future__ import annotations

from typing import Any

from crawler.source.line import Line
from crawler.source.presets import SourcePreset, get_preset, list_presets
from crawler.source.source import Source, SourceType


def generate_crawler_config(
    source: Source,
    lines: list[Line] | None = None,
    *,
    overrides: dict[str, Any] | None = None,
) -> "CrawlerConfig":
    from crawler.crawler.crawler import build_crawler_config

    return build_crawler_config(source, lines, overrides=overrides)


__all__ = [
    "Line",
    "Source",
    "SourcePreset",
    "SourceType",
    "generate_crawler_config",
    "get_preset",
    "list_presets",
]
