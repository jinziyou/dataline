"""采集任务 API：触发采集、查询任务状态与结果"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from server.core.database import get_session
from server.models.source import SourceModel, LineModel
from server.models.task import CrawlerTaskModel, CollectedDataModel
from server.schemas.task import (
    CrawlerTaskRead,
    CrawlerTaskTrigger,
    CollectedDataRead,
    PaginatedResponse,
)
from server.services.crawler_service import trigger_crawl

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _enrich_task(session: Session, task: CrawlerTaskModel) -> CrawlerTaskRead:
    source = session.get(SourceModel, task.source_id)
    return CrawlerTaskRead(
        **task.model_dump(),
        source_name=source.name if source else task.source_id,
    )


@router.post("", response_model=CrawlerTaskRead, status_code=201)
def create_task(
    body: CrawlerTaskTrigger,
    session: Session = Depends(get_session),
) -> CrawlerTaskRead:
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
    return _enrich_task(session, task)


@router.get("", response_model=PaginatedResponse[CrawlerTaskRead])
def list_tasks(
    source_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> PaginatedResponse[CrawlerTaskRead]:
    count_stmt = select(func.count()).select_from(CrawlerTaskModel)
    data_stmt = select(CrawlerTaskModel).order_by(CrawlerTaskModel.created_at.desc())
    if source_id:
        count_stmt = count_stmt.where(CrawlerTaskModel.source_id == source_id)
        data_stmt = data_stmt.where(CrawlerTaskModel.source_id == source_id)
    if status:
        count_stmt = count_stmt.where(CrawlerTaskModel.status == status)
        data_stmt = data_stmt.where(CrawlerTaskModel.status == status)
    total = session.exec(count_stmt).one()
    tasks = list(session.exec(data_stmt.offset(offset).limit(limit)).all())
    return PaginatedResponse(
        items=[_enrich_task(session, t) for t in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=CrawlerTaskRead)
def get_task(task_id: str, session: Session = Depends(get_session)) -> CrawlerTaskRead:
    task = session.get(CrawlerTaskModel, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return _enrich_task(session, task)


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
