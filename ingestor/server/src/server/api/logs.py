"""采集日志查询 API"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from server.core.database import get_session
from server.models.log import CrawlerLogModel

router = APIRouter(prefix="/logs", tags=["logs"])


class LogRead(BaseModel):
    id: int
    task_id: str
    source_id: str
    level: str
    message: str
    created_at: datetime


@router.get("", response_model=list[LogRead])
def list_logs(
    task_id: str | None = None,
    source_id: str | None = None,
    level: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[CrawlerLogModel]:
    stmt = select(CrawlerLogModel).order_by(CrawlerLogModel.created_at.desc())
    if task_id:
        stmt = stmt.where(CrawlerLogModel.task_id == task_id)
    if source_id:
        stmt = stmt.where(CrawlerLogModel.source_id == source_id)
    if level:
        stmt = stmt.where(CrawlerLogModel.level == level)
    stmt = stmt.offset(offset).limit(limit)
    return list(session.exec(stmt).all())
