"""采集日志查询 API"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select, func

from server.core.database import get_session
from server.models.log import CrawlerLogModel
from server.schemas.task import PaginatedResponse

router = APIRouter(prefix="/logs", tags=["logs"])


class LogRead(BaseModel):
    id: int
    task_id: str
    source_id: str
    level: str
    message: str
    created_at: datetime


@router.get("", response_model=PaginatedResponse[LogRead])
def list_logs(
    task_id: str | None = None,
    source_id: str | None = None,
    level: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> PaginatedResponse[LogRead]:
    count_stmt = select(func.count()).select_from(CrawlerLogModel)
    data_stmt = select(CrawlerLogModel).order_by(CrawlerLogModel.created_at.desc())
    if task_id:
        count_stmt = count_stmt.where(CrawlerLogModel.task_id == task_id)
        data_stmt = data_stmt.where(CrawlerLogModel.task_id == task_id)
    if source_id:
        count_stmt = count_stmt.where(CrawlerLogModel.source_id == source_id)
        data_stmt = data_stmt.where(CrawlerLogModel.source_id == source_id)
    if level:
        count_stmt = count_stmt.where(CrawlerLogModel.level == level)
        data_stmt = data_stmt.where(CrawlerLogModel.level == level)
    total = session.exec(count_stmt).one()
    logs = list(session.exec(data_stmt.offset(offset).limit(limit)).all())
    return PaginatedResponse(
        items=[LogRead.model_validate(log, from_attributes=True) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )
