"""SQLAlchemy async engine + session factory.

Uso típico:

    from vigia_shared.db import session_scope

    async with session_scope() as session:
        result = await session.execute(...)

Implementación: creamos un engine fresco por scope. Esto es importante cuando
las tasks de Celery usan `asyncio.run()` por invocación — un engine global
queda atado al primer event loop y revienta con "Event loop is closed" en la
siguiente. El costo de crear/disponer engine por scope es bajo (asyncpg pool
con 1-2 conns), y la API real reusa engine al estar dentro de un solo loop.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_DEFAULT_URL = "postgresql+asyncpg://vigia:vigia@localhost:5432/vigia"


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", _DEFAULT_URL)


def make_engine():
    return create_async_engine(
        get_database_url(),
        future=True,
        pool_pre_ping=True,
        echo=False,
    )


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    engine = make_engine()
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with Session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()
