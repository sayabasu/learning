from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from .core.config import get_settings


def _create_sqlite_directory(database_url: str) -> None:
    if database_url.startswith("sqlite"):
        _, _, path = database_url.partition("///")
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)


settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


def init_db() -> None:
    _create_sqlite_directory(settings.database_url)
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    with session_scope() as session:
        yield session
