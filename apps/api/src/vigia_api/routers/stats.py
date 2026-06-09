"""KPIs y agregaciones para el Dashboard y el Tracker DNU."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from vigia_api.core.db import get_sessionmaker
from vigia_shared.schemas import DashboardStats, DnuStats, SectorStat, TipoStat

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard() -> DashboardStats:
    Session = get_sessionmaker()
    async with Session() as session:
        total = (await session.execute(text("SELECT COUNT(*) FROM norma"))).scalar_one()
        por_tipo = (
            await session.execute(
                text("SELECT tipo, COUNT(*) c FROM norma GROUP BY tipo ORDER BY c DESC")
            )
        ).all()
        por_sector = (
            await session.execute(
                text(
                    "SELECT sector, COUNT(*) c FROM norma "
                    "WHERE sector IS NOT NULL GROUP BY sector ORDER BY c DESC"
                )
            )
        ).all()
    return DashboardStats(
        total_normas=int(total or 0),
        por_tipo=[TipoStat(tipo=r[0], cantidad=int(r[1])) for r in por_tipo],
        por_sector=[SectorStat(sector=r[0], cantidad=int(r[1])) for r in por_sector],
    )


@router.get("/dnu", response_model=DnuStats)
async def dnu_stats() -> DnuStats:
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT estado_bicameral, COUNT(*) c "
                    "FROM dnu_tracking GROUP BY estado_bicameral"
                )
            )
        ).all()
    by = {r[0]: int(r[1]) for r in rows}
    return DnuStats(
        total=sum(by.values()),
        aprobados=by.get("aprobado", 0),
        rechazados=by.get("rechazado", 0),
        pendientes=by.get("pendiente", 0),
    )
