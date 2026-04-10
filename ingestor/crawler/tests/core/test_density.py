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


# ---------------------------------------------------------------------------
# 时间检测：扩展模式
# ---------------------------------------------------------------------------


def test_detect_time_from_datetime_attribute() -> None:
    """无 <time> 标签时，含 datetime 属性的元素可作为时间选择器。"""
    html = '<span class="publish-time" datetime="2025-01-15">2025年1月15日</span>'
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(html)
    assert result.time_selector is not None


def test_detect_time_from_extended_class_names() -> None:
    """扩展 class 名列表中的常见时间 class 均可被检测。"""
    for cls in ("pubdate", "timestamp", "post-date", "update-time", "create-time"):
        html = f'<div class="{cls}">2025-01-15</div>'
        detector = DensityBasedDetector()
        result = detector.detect_from_detail(html)
        assert result.time_selector == f".{cls}", f"Expected .{cls} but got {result.time_selector}"


def test_detect_time_prefers_time_tag_over_datetime_attr() -> None:
    """<time> 标签优先级高于 datetime 属性。"""
    html = """
    <span datetime="2025-01-01">span with datetime</span>
    <time>2025-01-15</time>
    """
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(html)
    assert result.time_selector == "time"


# ---------------------------------------------------------------------------
# 内容检测：密度优于范围
# ---------------------------------------------------------------------------


def test_detect_content_avoids_navigation_heavy_divs() -> None:
    """链接密度高的导航区不应被选为内容区。"""
    html = """
    <div class="nav-links">
        <a href="/p1">Link 1</a><a href="/p2">Link 2</a><a href="/p3">Link 3</a>
        <a href="/p4">Link 4</a><a href="/p5">Link 5</a><a href="/p6">Link 6</a>
        <a href="/p7">Link 7</a><a href="/p8">Link 8</a><a href="/p9">Link 9</a>
    </div>
    <div id="article">
        <p>这是正文区域，包含了非常丰富的文章内容。通过信息密度分析，
        这一段落的文字与 HTML 标签的比例远高于纯链接导航区域。
        继续补充内容以确保此区域能被密度检测算法正确识别为正文。</p>
    </div>
    """
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(html)
    assert result.content_selector is not None
    assert "nav" not in (result.content_selector or "")


def test_detect_content_prefers_semantic_over_density_fallback() -> None:
    """有语义标签（article）时优先使用，而不走密度回退。"""
    html = """
    <div id="giant">
        这里有一大堆重复文字填充内容来使这个 div 的文本非常长，以便测试密度检测算法。
        重复重复重复重复重复重复重复重复重复重复重复重复重复重复重复重复重复重复。
    </div>
    <article>
        这是语义正文标签，内容足够丰富，应该被优先选择。本文探讨了各种技术话题的
        深层逻辑和实现细节，涵盖了从架构设计到具体编码的各个方面，为读者提供了
        全面而深入的技术视角。此处的文字数量已超过一百个字符，满足密度检测阈值。
    </article>
    """
    detector = DensityBasedDetector()
    result = detector.detect_from_detail(html)
    assert result.content_selector == "article"
