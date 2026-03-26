"""采集任务 API：触发采集、查询任务状态与结果"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from server.core.database import get_session
from server.models.source import SourceModel, LineModel
from server.models.task import CrawlerTaskModel, CollectedDataModel
from server.schemas.task import CrawlerTaskRead, CrawlerTaskTrigger, CollectedDataRead
from server.services.crawler_service import trigger_crawl

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=CrawlerTaskRead, status_code=201)
def create_task(
    body: CrawlerTaskTrigger,
    session: Session = Depends(get_session),
) -> CrawlerTaskModel:
    """触发一次采集任务"""
    source = session.get(SourceModel, body.source_id)
    if not source:
        raise HTTPException(404, "Source not found")

    lines = list(
        session.exec(
            select(LineModel)
            .where(LineModel.source_id == body.source_id)
            .where(LineModel.enabled == True)  # noqa: E712
        ).all()
    )
    if not lines:
        raise HTTPException(400, "No enabled lines for this source")

    task = trigger_crawl(session, source, lines, body.overrides or None)
    return task


@router.get("", response_model=list[CrawlerTaskRead])
def list_tasks(
    source_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[CrawlerTaskModel]:
    stmt = select(CrawlerTaskModel).order_by(CrawlerTaskModel.created_at.desc())
    if source_id:
        stmt = stmt.where(CrawlerTaskModel.source_id == source_id)
    if status:
        stmt = stmt.where(CrawlerTaskModel.status == status)
    stmt = stmt.offset(offset).limit(limit)
    return list(session.exec(stmt).all())


@router.get("/{task_id}", response_model=CrawlerTaskRead)
def get_task(task_id: str, session: Session = Depends(get_session)) -> CrawlerTaskModel:
    task = session.get(CrawlerTaskModel, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.get("/{task_id}/data", response_model=list[CollectedDataRead])
def get_task_data(
    task_id: str,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[CollectedDataModel]:
    stmt = (
        select(CollectedDataModel)
        .where(CollectedDataModel.task_id == task_id)
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(stmt).all())
