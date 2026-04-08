"""系统统计概览 API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select, func, col

from server.core.database import get_session
from server.models.source import SourceModel
from server.models.task import CrawlerTaskModel, CollectedDataModel
from server.models.log import CrawlerLogModel

router = APIRouter(prefix="/stats", tags=["stats"])


class TaskStatusCounts(BaseModel):
    pending: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0


class StatsOverview(BaseModel):
    source_count: int
    enabled_source_count: int
    task_count: int
    task_status_counts: TaskStatusCounts
    total_collected_items: int
    log_count: int
    recent_tasks: list[dict]


@router.get("", response_model=StatsOverview)
def get_stats(session: Session = Depends(get_session)) -> StatsOverview:
    source_count = session.exec(
        select(func.count()).select_from(SourceModel)
    ).one()
    enabled_source_count = session.exec(
        select(func.count()).select_from(SourceModel).where(SourceModel.enabled == True)  # noqa: E712
    ).one()

    task_count = session.exec(
        select(func.count()).select_from(CrawlerTaskModel)
    ).one()

    status_rows = session.exec(
        select(CrawlerTaskModel.status, func.count())
        .group_by(CrawlerTaskModel.status)
    ).all()
    status_map = {row[0]: row[1] for row in status_rows}
    task_status_counts = TaskStatusCounts(
        pending=status_map.get("pending", 0),
        running=status_map.get("running", 0),
        success=status_map.get("success", 0),
        failed=status_map.get("failed", 0),
    )

    total_collected = session.exec(
        select(func.count()).select_from(CollectedDataModel)
    ).one()

    log_count = session.exec(
        select(func.count()).select_from(CrawlerLogModel)
    ).one()

    recent_task_models = list(
        session.exec(
            select(CrawlerTaskModel)
            .order_by(col(CrawlerTaskModel.created_at).desc())
            .limit(5)
        ).all()
    )
    recent_tasks = []
    for t in recent_task_models:
        source = session.get(SourceModel, t.source_id)
        recent_tasks.append({
            "id": t.id,
            "source_id": t.source_id,
            "source_name": source.name if source else t.source_id,
            "status": t.status,
            "total_items": t.total_items,
            "created_at": t.created_at.isoformat(),
        })

    return StatsOverview(
        source_count=source_count,
        enabled_source_count=enabled_source_count,
        task_count=task_count,
        task_status_counts=task_status_counts,
        total_collected_items=total_collected,
        log_count=log_count,
        recent_tasks=recent_tasks,
    )
