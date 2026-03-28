"""
Crawler 编排服务

通过 crawler 库接口调用采集能力，管理采集任务的生命周期。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from sqlmodel import Session

from crawler import Crawler, CrawlerResult, CrawlerRunner, Line, Source, SourceType

from server.models.source import SourceModel, LineModel
from server.models.task import CrawlerTaskModel, CollectedDataModel
from server.models.log import CrawlerLogModel

logger = logging.getLogger(__name__)


def _to_domain_line(m: LineModel) -> Line:
    return Line(
        id=m.id,
        source_id=m.source_id,
        name=m.name,
        url=m.url,
        description=m.description,
        enabled=m.enabled,
        meta=m.meta or {},
    )


def _to_domain_source(m: SourceModel, line_models: list[LineModel]) -> Source:
    return Source(
        id=m.id,
        name=m.name,
        type=SourceType(m.type),
        url=m.url,
        description=m.description,
        enabled=m.enabled,
        meta=m.meta or {},
        lines=[_to_domain_line(lm) for lm in line_models],
    )


async def run_crawler_for_source(
    source_model: SourceModel,
    line_models: list[LineModel],
    overrides: dict | None = None,
) -> CrawlerResult:
    """调用 crawler 库执行采集（以 ``Crawler`` 为入口）。"""
    source = _to_domain_source(source_model, line_models)
    return await Crawler.run_source(source, overrides=overrides or {})


def trigger_crawl(
    session: Session,
    source_model: SourceModel,
    line_models: list[LineModel],
    overrides: dict | None = None,
) -> CrawlerTaskModel:
    """
    触发一次采集任务：
    1. 创建 CrawlerTaskModel 记录
    2. 后台异步执行采集
    3. 采集完成后写入结果与日志
    """
    task_id = f"ct-{uuid.uuid4().hex[:12]}"
    task_model = CrawlerTaskModel(
        id=task_id,
        source_id=source_model.id,
        status="running",
        config={},
        created_at=datetime.now(),
        started_at=datetime.now(),
    )
    session.add(task_model)
    session.commit()
    session.refresh(task_model)

    asyncio.create_task(
        _execute_and_save(task_id, source_model, line_models, overrides)
    )

    return task_model


async def _execute_and_save(
    task_id: str,
    source_model: SourceModel,
    line_models: list[LineModel],
    overrides: dict | None,
) -> None:
    """后台执行采集并持久化结果"""
    from server.core.database import get_session

    try:
        result = await run_crawler_for_source(source_model, line_models, overrides)

        session_gen = get_session()
        session = next(session_gen)
        try:
            task_model = session.get(CrawlerTaskModel, task_id)
            if task_model:
                task_model.status = "success"
                task_model.total_items = result.total_items
                task_model.success_count = result.success_count
                task_model.failed_count = result.failed_count
                task_model.finished_at = datetime.now()
                task_model.config = result.model_dump(
                    mode="json", include={"crawler_id", "source_id"}
                )

                for tr in result.task_results:
                    for item in tr.items:
                        data_model = CollectedDataModel(
                            id=item.id,
                            task_id=task_id,
                            source_id=item.source_id,
                            line_id=item.line_id,
                            url=item.url,
                            title=item.title,
                            content=item.content[:10000],
                            content_type=item.content_type,
                            raw=item.raw,
                            meta=item.meta,
                            collected_at=item.collected_at,
                        )
                        session.add(data_model)

                log = CrawlerLogModel(
                    task_id=task_id,
                    source_id=source_model.id,
                    level="INFO",
                    message=f"Crawl completed: {result.total_items} items",
                )
                session.add(log)
                session.commit()
        finally:
            try:
                next(session_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error("Crawl task %s failed: %s", task_id, e)
        session_gen = get_session()
        session = next(session_gen)
        try:
            task_model = session.get(CrawlerTaskModel, task_id)
            if task_model:
                task_model.status = "failed"
                task_model.error = str(e)
                task_model.finished_at = datetime.now()

            log = CrawlerLogModel(
                task_id=task_id,
                source_id=source_model.id,
                level="ERROR",
                message=f"Crawl failed: {e}",
            )
            session.add(log)
            session.commit()
        finally:
            try:
                next(session_gen)
            except StopIteration:
                pass
