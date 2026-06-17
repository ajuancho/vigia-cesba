"""Radar societario: avisos de la 2ª sección del BORA (tabla aviso_societario).

Endpoints públicos (datos abiertos), separados del corpus `norma` a propósito:
constituciones, asambleas y edictos son otra superficie de producto.
"""
from __future__ import annotations

from datetime import date as Date
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, text

from vigia_api.core.db import get_sessionmaker
from vigia_shared.models import AvisoSocietario

router = APIRouter(prefix="/avisos", tags=["avisos"])


class AvisoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aviso_id: str
    fecha: Date | None
    razon_social: str | None
    rubro: str | None
    url: str | None
    ingested_at: datetime | None = None


class AvisoPage(BaseModel):
    items: list[AvisoOut]
    total: int
    limit: int
    offset: int


@router.get("", response_model=AvisoPage)
async def list_avisos(
    q: str | None = Query(None, description="búsqueda FTS (razón social, rubro, texto)"),
    rubro: str | None = Query(None, description="prefijo de rubro, p.ej. SOCIEDADES ANONIMAS"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
) -> AvisoPage:
    Session = get_sessionmaker()
    filters = []
    if q:
        filters.append(
            text("search_vector @@ plainto_tsquery('spanish', :q)").bindparams(q=q)
        )
    if rubro:
        filters.append(AvisoSocietario.rubro.ilike(f"{rubro}%"))

    async with Session() as session:
        total = (
            await session.execute(
                select(func.count()).select_from(AvisoSocietario).where(*filters)
            )
        ).scalar_one()
        rows = (
            await session.execute(
                select(AvisoSocietario)
                .where(*filters)
                .order_by(AvisoSocietario.fecha.desc(), AvisoSocietario.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()

    return AvisoPage(
        items=[AvisoOut.model_validate(r) for r in rows],
        total=int(total or 0),
        limit=limit,
        offset=offset,
    )


class AvisoStats(BaseModel):
    total_historico: int
    semana: int
    semana_anterior: int
    mes: int
    mes_anterior: int
    rubros_distintos: int
    por_rubro: list[dict]  # últimos 30 días, [{rubro, cantidad}] desc
    serie: list[dict]      # últimas 12 semanas, [{semana: 'YYYY-MM-DD', total}]


@router.get("/stats", response_model=AvisoStats)
async def avisos_stats() -> AvisoStats:
    """Panel del Radar societario: KPIs (semana/mes con su período previo para el
    delta), serie semanal (12 semanas) y desglose por rubro (30 días, para la
    torta). Calca el shape de `/stats/dashboard` del corpus normativo."""
    Session = get_sessionmaker()
    async with Session() as session:
        kpi = (
            await session.execute(
                text(
                    """
                    SELECT
                      COUNT(*) AS total_historico,
                      COUNT(*) FILTER (WHERE fecha > CURRENT_DATE - 7) AS semana,
                      COUNT(*) FILTER (WHERE fecha > CURRENT_DATE - 14 AND fecha <= CURRENT_DATE - 7) AS semana_anterior,
                      COUNT(*) FILTER (WHERE fecha > CURRENT_DATE - 30) AS mes,
                      COUNT(*) FILTER (WHERE fecha > CURRENT_DATE - 60 AND fecha <= CURRENT_DATE - 30) AS mes_anterior,
                      COUNT(DISTINCT rubro) FILTER (WHERE fecha > CURRENT_DATE - 30) AS rubros_distintos
                    FROM aviso_societario
                    """
                )
            )
        ).one()
        por_rubro = (
            await session.execute(
                text(
                    """
                    SELECT COALESCE(rubro, 'Sin rubro') AS rubro, COUNT(*) AS c
                    FROM aviso_societario
                    WHERE fecha > CURRENT_DATE - 30
                    GROUP BY 1 ORDER BY c DESC
                    """
                )
            )
        ).all()
        serie = (
            await session.execute(
                text(
                    """
                    SELECT to_char(date_trunc('week', fecha), 'YYYY-MM-DD') AS semana,
                           COUNT(*) AS total
                    FROM aviso_societario
                    WHERE fecha > CURRENT_DATE - 84
                    GROUP BY 1 ORDER BY 1
                    """
                )
            )
        ).all()

    return AvisoStats(
        total_historico=int(kpi.total_historico or 0),
        semana=int(kpi.semana or 0),
        semana_anterior=int(kpi.semana_anterior or 0),
        mes=int(kpi.mes or 0),
        mes_anterior=int(kpi.mes_anterior or 0),
        rubros_distintos=int(kpi.rubros_distintos or 0),
        por_rubro=[{"rubro": r[0], "cantidad": int(r[1])} for r in por_rubro],
        serie=[{"semana": r[0], "total": int(r[1])} for r in serie],
    )


@router.get("/rubros")
async def rubros(days: int = Query(30, ge=1, le=365)) -> list[dict]:
    """Rubros con actividad reciente (para el filtro del Radar societario)."""
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT rubro, COUNT(*) AS c FROM aviso_societario
                    WHERE rubro IS NOT NULL
                      AND fecha > CURRENT_DATE - make_interval(days => :days)
                    GROUP BY rubro ORDER BY c DESC LIMIT 30
                    """
                ),
                {"days": days},
            )
        ).all()
    return [{"rubro": r[0], "cantidad": int(r[1])} for r in rows]
