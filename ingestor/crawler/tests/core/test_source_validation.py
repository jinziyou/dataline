"""Source 校验（不依赖具体 SourceType 行为）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crawler.source import Source


def test_source_validation_missing_required() -> None:
    with pytest.raises(ValidationError):
        Source.model_validate({"name": "x"})  # type: ignore[arg-type]
