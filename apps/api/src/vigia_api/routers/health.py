from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from vigia_api.core.db import get_sessionmaker

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/health/detailed")
async def health_detailed() -> dict:
    """Liveness + freshness por fuente + conteo de normas."""
    Session = get_sessionmaker()
    async with Session() as session:
        total = (await session.execute(text("SELECT COUNT(*) FROM norma"))).scalar_one()
        sources = (
            await session.execute(
                text(
                    "SELECT code, name, last_run_at, last_status "
                    "FROM source_catalog ORDER BY code"
                )
            )
        ).all()
    return {
        "status": "ok",
        "normas": int(total or 0),
        "sources": [
            {
                "code": s[0],
                "name": s[1],
                "last_run_at": s[2].isoformat() if s[2] else None,
                "last_status": s[3],
            }
            for s in sources
        ],
    }
