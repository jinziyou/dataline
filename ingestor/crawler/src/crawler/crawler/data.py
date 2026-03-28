"""
采集结果数据模型：Data

Line / Task 下的具体数据条目（如一篇文章、一条记录），对应 source->line->data 中的 data。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Data(BaseModel):
    """数据条目：通道下的具体数据"""
    id: str = Field(description="数据条目唯一标识")
    line_id: str = Field(description="所属通道 ID")
    source_id: str = Field(description="所属数据源 ID")
    url: str | None = Field(default=None, description="数据来源地址")
    title: str = Field(default="", description="数据标题")
    content: str = Field(default="", description="数据内容")
    content_type: str = Field(default="text/html", description="内容类型")
    raw: dict[str, Any] = Field(default_factory=dict, description="原始数据")
    meta: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    collected_at: datetime = Field(default_factory=datetime.now)
