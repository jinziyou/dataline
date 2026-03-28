"""URL 去重。"""

from __future__ import annotations

from crawler.crawler import UrlDeduplicator


def test_url_deduplicator_marks_and_detects_seen() -> None:
    d = UrlDeduplicator()
    url = "https://example.test/same"
    assert d.is_seen(url) is False
    d.mark_seen(url)
    assert d.is_seen(url) is True


def test_url_deduplicator_reset() -> None:
    d = UrlDeduplicator()
    d.mark_seen("https://a.test")
    d.reset()
    assert d.is_seen("https://a.test") is False
