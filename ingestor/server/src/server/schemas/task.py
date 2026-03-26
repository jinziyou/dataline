"""采集任务与结果的请求/响应 Schema"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CrawlerTaskTrigger(BaseModel):
    source_id: str = Field(max_length=64)
    overrides: dict[str, Any] = Field(default_factory=dict)


class CrawlerTaskRead(BaseModel):
    id: str
    source_id: str
    status: str
    config: dict[str, Any]
    total_items: int
    success_count: int
    failed_count: int
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class CollectedDataRead(BaseModel):
    id: str
    task_id: str
    source_id: str
    line_id: str
    url: str | None
    title: str
    content: str
    content_type: str
    raw: dict[str, Any]
    meta: dict[str, Any]
    collected_at: datetime
