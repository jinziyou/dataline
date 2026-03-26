"""采集日志的数据库模型"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class CrawlerLogModel(SQLModel, table=True):
    __tablename__ = "crawler_logs"

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, max_length=64)
    source_id: str = Field(index=True, max_length=64)
    level: str = Field(default="INFO", max_length=16)
    message: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)
