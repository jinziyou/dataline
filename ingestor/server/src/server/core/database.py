"""数据库连接与会话管理"""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from server.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
