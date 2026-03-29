"""
数据源模型：Source

一个数据源整体（如某个网站、某个 API 服务），包含若干 Line（数据通道）。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from crawler.source.line import Line


class SourceType(str, Enum):
    """五大类数据源分类"""
    WEBSITE = "website"
    API = "api"
    FILE = "file"
    STREAM = "stream"
    EXTERNAL = "external"


class Source(BaseModel):
    """数据源：一个数据源整体，内含多条 Line。"""
    id: str = Field(description="数据源唯一标识")
    name: str = Field(description="数据源名称")
    type: SourceType = Field(description="数据源类型")
    url: str | None = Field(default=None, description="数据源地址")
    description: str = Field(default="", description="数据源描述")
    enabled: bool = Field(default=True, description="是否启用")
    meta: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    lines: list[Line] = Field(
        default_factory=list,
        description="下属数据通道列表，至少一条；未指定时自动创建默认 Line（url 与 source.url 一致）",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def _default_lines_and_source_id(self) -> Source:
        if not self.lines:
            self.lines = [
                Line(
                    id=f"{self.id}-default-line",
                    source_id=self.id,
                    name="default",
                    url=self.url,
                )
            ]
        self.lines = [
            line.model_copy(update={"source_id": self.id}) if line.source_id != self.id else line
            for line in self.lines
        ]
        return self
