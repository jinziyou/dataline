"""DensityBasedDetector：信息密度选择器自动检测。"""

from __future__ import annotations

from crawler.crawler.density import DensityBasedDetector

LISTING_HTML = """
<html><body>
<nav><a href="/about">About</a></nav>
<div class="news-list">
    <div class="item"><a href="/news/1">News 1</a></div>
    <div class="item"><a href="/news/2">News 2</a></div>
    <div class="item"><a href="/news/3">News 3</a></div>
    <div class="item"><a href="/news/4">News 4</a></div>
</div>
</body></html>
"""

DETAIL_HTML = """
<html><body>
<h1 class="article-title">大标题</h1>
<time datetime="2025-06-01">2025年6月1日</time>
<article class="content">
    <p>这是正文第一段，内容非常丰富，包含了很多有价值的信息。我们在这段文字中详细描述了事件的来龙去脉。</p>
    <p>这是正文第二段，继续补充说明前文提到的内容。通过深入分析，我们可以看到这一事件的重要性和深远影响。</p>
    <p>这是正文第三段，总结全文要点。综合以上分析，我们得出了明确的结论，并提出了未来的发展方向和建议。</p>
</article>
</body></html>
"""


def test_detect_link_pattern_from_listing() -> None:
    detector = DensityBasedDetector()
    selectors = detector.detect_from_listing(LISTING_HTML)
    assert len(selectors) >= 1
    assert "a" in selectors[0]


def test_detect_no_pattern_when_few_links() -> None:
    html = '<a href="/one">One</a><a href="/two">Two</a>'
    detector = DensityBasedDetector()
    selectors = detector.detect_from_listing(html)
    assert selectors == []


def test_detect_title_from_detail() -> None:
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(DETAIL_HTML)
    assert result.title_selector is not None
    assert "h1" in result.title_selector


def test_detect_time_from_detail() -> None:
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(DETAIL_HTML)
    assert result.time_selector == "time"


def test_detect_content_from_detail() -> None:
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(DETAIL_HTML)
    assert result.content_selector is not None


def test_detect_time_from_class() -> None:
    html = '<div class="date">2025-01-01</div>'
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(html)
    assert result.time_selector == ".date"


def test_detect_nothing_from_empty_html() -> None:
    detector = DensityBasedDetector()
    listing = detector.detect_from_listing("")
    detail = detector.detect_from_detail("")
    assert listing == []
    assert detail.title_selector is None
    assert detail.time_selector is None
    assert detail.content_selector is None


def test_detect_content_by_density() -> None:
    """即使没有语义标签，也能通过文本密度找到正文容器。"""
    html = """
    <div id="sidebar">Short</div>
    <div id="main-content">
        <p>这是一段非常长的正文内容，包含了大量有价值的信息。
        这里持续输出足够多的文字来确保密度检测能够识别这个区域。
        继续添加更多内容以满足阈值要求。这段内容的长度远超一百字符。</p>
    </div>
    """
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(html)
    assert result.content_selector is not None
