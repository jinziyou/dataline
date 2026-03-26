"""数据源与通道的请求/响应 Schema"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    id: str = Field(max_length=64)
    name: str = Field(max_length=256)
    type: str = Field(max_length=32)
    url: str | None = None
    description: str = ""
    enabled: bool = True
    meta: dict[str, Any] = Field(default_factory=dict)


class SourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    description: str | None = None
    enabled: bool | None = None
    meta: dict[str, Any] | None = None


class SourceRead(BaseModel):
    id: str
    name: str
    type: str
    url: str | None
    description: str
    enabled: bool
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class LineCreate(BaseModel):
    id: str = Field(max_length=64)
    source_id: str = Field(max_length=64)
    name: str = Field(max_length=256)
    url: str | None = None
    description: str = ""
    enabled: bool = True
    meta: dict[str, Any] = Field(default_factory=dict)


class LineUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    description: str | None = None
    enabled: bool | None = None
    meta: dict[str, Any] | None = None


class LineRead(BaseModel):
    id: str
    source_id: str
    name: str
    url: str | None
    description: str
    enabled: bool
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime
