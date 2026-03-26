"""数据源与通道 CRUD API"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from server.core.database import get_session
from server.models.source import SourceModel, LineModel
from server.schemas.source import (
    SourceCreate,
    SourceUpdate,
    SourceRead,
    LineCreate,
    LineUpdate,
    LineRead,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
def list_sources(
    enabled: bool | None = None,
    session: Session = Depends(get_session),
) -> list[SourceModel]:
    stmt = select(SourceModel)
    if enabled is not None:
        stmt = stmt.where(SourceModel.enabled == enabled)
    return list(session.exec(stmt).all())


@router.get("/{source_id}", response_model=SourceRead)
def get_source(source_id: str, session: Session = Depends(get_session)) -> SourceModel:
    source = session.get(SourceModel, source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    return source


@router.post("", response_model=SourceRead, status_code=201)
def create_source(
    body: SourceCreate,
    session: Session = Depends(get_session),
) -> SourceModel:
    if session.get(SourceModel, body.id):
        raise HTTPException(409, "Source already exists")
    source = SourceModel.model_validate(body)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceRead)
def update_source(
    source_id: str,
    body: SourceUpdate,
    session: Session = Depends(get_session),
) -> SourceModel:
    source = session.get(SourceModel, source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(source, k, v)
    source.updated_at = datetime.now()
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: str, session: Session = Depends(get_session)) -> None:
    source = session.get(SourceModel, source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    session.delete(source)
    session.commit()


# --- Lines ---

@router.get("/{source_id}/lines", response_model=list[LineRead])
def list_lines(
    source_id: str,
    session: Session = Depends(get_session),
) -> list[LineModel]:
    stmt = select(LineModel).where(LineModel.source_id == source_id)
    return list(session.exec(stmt).all())


@router.post("/{source_id}/lines", response_model=LineRead, status_code=201)
def create_line(
    source_id: str,
    body: LineCreate,
    session: Session = Depends(get_session),
) -> LineModel:
    if not session.get(SourceModel, source_id):
        raise HTTPException(404, "Source not found")
    line = LineModel.model_validate({**body.model_dump(), "source_id": source_id})
    session.add(line)
    session.commit()
    session.refresh(line)
    return line


@router.patch("/lines/{line_id}", response_model=LineRead)
def update_line(
    line_id: str,
    body: LineUpdate,
    session: Session = Depends(get_session),
) -> LineModel:
    line = session.get(LineModel, line_id)
    if not line:
        raise HTTPException(404, "Line not found")
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(line, k, v)
    line.updated_at = datetime.now()
    session.add(line)
    session.commit()
    session.refresh(line)
    return line


@router.delete("/lines/{line_id}", status_code=204)
def delete_line(line_id: str, session: Session = Depends(get_session)) -> None:
    line = session.get(LineModel, line_id)
    if not line:
        raise HTTPException(404, "Line not found")
    session.delete(line)
    session.commit()
