"""采集任务与结果的数据库模型"""

from datetime import datetime

from sqlmodel import Field, SQLModel, JSON, Column


class CrawlerTaskModel(SQLModel, table=True):
    __tablename__ = "crawler_tasks"

    id: str = Field(primary_key=True, max_length=64)
    source_id: str = Field(foreign_key="sources.id", index=True, max_length=64)
    status: str = Field(default="pending", index=True, max_length=32)
    config: dict = Field(default_factory=dict, sa_column=Column(JSON, default={}))
    total_items: int = Field(default=0)
    success_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    error: str | None = Field(default=None)
    started_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


class CollectedDataModel(SQLModel, table=True):
    __tablename__ = "collected_data"

    id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(foreign_key="crawler_tasks.id", index=True, max_length=64)
    source_id: str = Field(foreign_key="sources.id", index=True, max_length=64)
    line_id: str = Field(index=True, max_length=64)
    url: str | None = Field(default=None, max_length=2048)
    title: str = Field(default="")
    content: str = Field(default="")
    content_type: str = Field(default="text/html", max_length=128)
    raw: dict = Field(default_factory=dict, sa_column=Column(JSON, default={}))
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON, default={}))
    collected_at: datetime = Field(default_factory=datetime.now)
