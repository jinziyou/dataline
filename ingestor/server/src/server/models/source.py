"""数据源与通道的数据库模型"""

from datetime import datetime

from sqlmodel import Field, SQLModel, JSON, Column


class SourceModel(SQLModel, table=True):
    __tablename__ = "sources"

    id: str = Field(primary_key=True, max_length=64)
    name: str = Field(max_length=256)
    type: str = Field(max_length=32, index=True)
    url: str | None = Field(default=None, max_length=2048)
    description: str = Field(default="")
    enabled: bool = Field(default=True, index=True)
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON, default={}))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LineModel(SQLModel, table=True):
    __tablename__ = "lines"

    id: str = Field(primary_key=True, max_length=64)
    source_id: str = Field(foreign_key="sources.id", index=True, max_length=64)
    name: str = Field(max_length=256)
    url: str | None = Field(default=None, max_length=2048)
    description: str = Field(default="")
    enabled: bool = Field(default=True, index=True)
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON, default={}))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
