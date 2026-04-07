"""ExtractorConfig 模型测试。"""

from __future__ import annotations

from crawler.crawler.task import ExtractorConfig


def test_default_config_empty() -> None:
    cfg = ExtractorConfig()
    assert cfg.link_selectors == []
    assert cfg.title_selector is None
    assert cfg.time_selector is None
    assert cfg.content_selector is None


def test_has_data_selectors_false_when_all_none() -> None:
    assert ExtractorConfig().has_data_selectors is False


def test_has_data_selectors_true_with_title() -> None:
    assert ExtractorConfig(title_selector="h1").has_data_selectors is True


def test_has_data_selectors_true_with_content() -> None:
    assert ExtractorConfig(content_selector=".body").has_data_selectors is True


def test_has_data_selectors_true_with_time() -> None:
    assert ExtractorConfig(time_selector="time").has_data_selectors is True


def test_validate_from_dict() -> None:
    cfg = ExtractorConfig.model_validate({
        "link_selectors": [".list a", ".sub-list a"],
        "title_selector": "h1",
        "time_selector": ".date",
        "content_selector": ".content",
    })
    assert cfg.link_selectors == [".list a", ".sub-list a"]
    assert cfg.title_selector == "h1"


def test_validate_from_partial_dict() -> None:
    cfg = ExtractorConfig.model_validate({"link_selectors": [".news a"]})
    assert cfg.link_selectors == [".news a"]
    assert cfg.title_selector is None
