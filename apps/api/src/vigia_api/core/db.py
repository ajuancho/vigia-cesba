"""Async engine para la API (singleton — vive dentro del único event loop de uvicorn)."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from vigia_shared.db import get_database_url

_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            future=True,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            echo=False,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    return _sessionmaker
