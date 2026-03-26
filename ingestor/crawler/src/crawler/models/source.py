"""
数据抽象模型：source -> line -> data

将多源异类数据统一抽象为三层结构：
- Source: 一个数据源整体（如某个网站、某个 API 服务）
- Line:   数据源下的一条数据通道（如网站的一个栏目、API 的一个端点）
- DataItem: 通道下的具体数据条目（如一篇文章、一条记录）
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """五大类数据源分类"""
    WEBSITE = "website"
    API = "api"
    FILE = "file"
    STREAM = "stream"
    EXTERNAL = "external"


class Source(BaseModel):
    """数据源：一个数据源整体"""
    id: str = Field(description="数据源唯一标识")
    name: str = Field(description="数据源名称")
    type: SourceType = Field(description="数据源类型")
    url: str | None = Field(default=None, description="数据源地址")
    description: str = Field(default="", description="数据源描述")
    enabled: bool = Field(default=True, description="是否启用")
    meta: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Line(BaseModel):
    """数据通道：数据源下的一条数据通道/导航路径"""
    id: str = Field(description="通道唯一标识")
    source_id: str = Field(description="所属数据源 ID")
    name: str = Field(description="通道名称")
    url: str | None = Field(default=None, description="通道地址（如导航页 URL、API 端点）")
    description: str = Field(default="", description="通道描述")
    enabled: bool = Field(default=True, description="是否启用")
    meta: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DataItem(BaseModel):
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
