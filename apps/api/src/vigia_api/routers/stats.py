"""KPIs y agregaciones para el Dashboard y el Tracker DNU."""
from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import text

from vigia_api.core.db import get_sessionmaker
from vigia_shared.schemas import (
    DashboardStats,
    DnuAnio,
    DnuStats,
    OrganismoStat,
    RecentStats,
    SectorStat,
    SeriesPoint,
    TipoStat,
)

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
        rec = (
            await session.execute(
                text(
                    """
                    SELECT
                      COUNT(*) FILTER (WHERE fecha_publicacion >= current_date - 7)  AS semana,
                      COUNT(*) FILTER (WHERE fecha_publicacion >= current_date - 14
                                         AND fecha_publicacion <  current_date - 7)  AS semana_anterior,
                      COUNT(*) FILTER (WHERE fecha_publicacion >= current_date - 30) AS mes,
                      COUNT(*) FILTER (WHERE fecha_publicacion >= current_date - 60
                                         AND fecha_publicacion <  current_date - 30) AS mes_anterior,
                      COUNT(*) FILTER (WHERE tipo = 'PROYECTO'
                                         AND fecha_publicacion >= current_date - 30) AS proyectos_30d,
                      COUNT(*) FILTER (WHERE tipo = 'DNU'
                                         AND fecha_publicacion >= date_trunc('year', current_date)) AS dnu_anio
                    FROM norma
                    WHERE fecha_publicacion >= current_date - 60
                       OR (tipo = 'DNU' AND fecha_publicacion >= date_trunc('year', current_date))
                    """
                )
            )
        ).one()
    return DashboardStats(
        total_normas=int(total or 0),
        por_tipo=[TipoStat(tipo=r[0], cantidad=int(r[1])) for r in por_tipo],
        por_sector=[SectorStat(sector=r[0], cantidad=int(r[1])) for r in por_sector],
        recientes=RecentStats(
            semana=int(rec.semana or 0),
            semana_anterior=int(rec.semana_anterior or 0),
            mes=int(rec.mes or 0),
            mes_anterior=int(rec.mes_anterior or 0),
            proyectos_30d=int(rec.proyectos_30d or 0),
            dnu_anio=int(rec.dnu_anio or 0),
        ),
    )


@router.get("/series", response_model=list[SeriesPoint])
async def series(months: int = Query(24, ge=3, le=120)) -> list[SeriesPoint]:
    """Producción normativa mensual por tipo (serie temporal del pulso regulatorio)."""
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT to_char(date_trunc('month', fecha_publicacion), 'YYYY-MM') AS mes,
                           tipo, COUNT(*) c
                    FROM norma
                    WHERE fecha_publicacion >= date_trunc('month', current_date) - make_interval(months => :months)
                      AND fecha_publicacion < date_trunc('month', current_date) + interval '1 month'
                    GROUP BY 1, 2
                    ORDER BY 1
                    """
                ),
                {"months": months},
            )
        ).all()

    by_month: dict[str, dict[str, int]] = {}
    for mes, tipo, c in rows:
        by_month.setdefault(mes, {})[tipo] = int(c)
    return [
        SeriesPoint(mes=mes, total=sum(tipos.values()), por_tipo=tipos)
        for mes, tipos in sorted(by_month.items())
    ]


@router.get("/organismos", response_model=list[OrganismoStat])
async def organismos(
    days: int = Query(90, ge=7, le=365),
    limit: int = Query(10, ge=3, le=30),
) -> list[OrganismoStat]:
    """Top organismos emisores del período reciente (quién está regulando)."""
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT organismo, COUNT(*) c
                    FROM norma
                    WHERE organismo IS NOT NULL
                      AND fecha_publicacion >= current_date - make_interval(days => :days)
                    GROUP BY organismo
                    ORDER BY c DESC
                    LIMIT :limit
                    """
                ),
                {"days": days, "limit": limit},
            )
        ).all()
    return [OrganismoStat(organismo=r[0], cantidad=int(r[1])) for r in rows]


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
        historico = (
            await session.execute(
                text(
                    """
                    SELECT EXTRACT(YEAR FROM fecha_publicacion)::int AS anio, COUNT(*) c
                    FROM norma
                    WHERE tipo = 'DNU' AND fecha_publicacion IS NOT NULL
                    GROUP BY 1
                    ORDER BY 1
                    """
                )
            )
        ).all()
    by = {r[0]: int(r[1]) for r in rows}
    return DnuStats(
        total=sum(by.values()),
        aprobados=by.get("aprobado", 0),
        rechazados=by.get("rechazado", 0),
        pendientes=by.get("pendiente", 0),
        historico=[DnuAnio(anio=int(r[0]), cantidad=int(r[1])) for r in historico],
    )
