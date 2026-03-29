"""
数据通道模型：Line

数据源下的一条数据通道/导航路径（如网站的一个栏目、API 的一个端点）。
``meta`` 为通道级扩展信息，由业务自行约定结构。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Line(BaseModel):
    """数据通道：数据源下的一条数据通道/导航路径"""
    id: str = Field(description="通道唯一标识")
    source_id: str = Field(description="所属数据源 ID")
    name: str = Field(description="通道名称")
    url: str | None = Field(default=None, description="通道地址（如导航页 URL、API 端点）")
    description: str = Field(default="", description="通道描述")
    enabled: bool = Field(default=True, description="是否启用")
    item_limit: int | None = Field(
        default=None,
        description="该通道允许产出的最大数据条数；未设置表示不设上限",
    )
    meta: dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
