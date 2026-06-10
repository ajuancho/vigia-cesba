"""Feed de normas + detalle. Lee de Postgres (poblado por el worker InfoLEG)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from vigia_api.core.db import get_sessionmaker
from vigia_shared.models import DnuTracking, Norma, SourceCatalog
from vigia_shared.schemas import NormaDetail, NormaListItem, NormaPage

router = APIRouter(prefix="/normas", tags=["normas"])


@router.get("", response_model=NormaPage)
async def list_normas(
    tipo: str | None = Query(None, description="DNU|DECRETO|LEY|RESOLUCION|DISPOSICION|PROYECTO|COMUNICACION|OTRA"),
    impacto: str | None = Query(None, description="alto|medio|bajo"),
    sector: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
) -> NormaPage:
    Session = get_sessionmaker()
    filters = []
    if tipo:
        filters.append(Norma.tipo == tipo)
    if impacto:
        filters.append(Norma.impacto == impacto)
    if sector:
        filters.append(Norma.sector == sector)

    async with Session() as session:
        total = (
            await session.execute(select(func.count()).select_from(Norma).where(*filters))
        ).scalar_one()
        query = (
            select(Norma)
            .where(*filters)
            .order_by(Norma.fecha_publicacion.desc().nullslast(), Norma.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if tipo == "DNU":
            # El tracker bicameral viaja con el listado solo cuando se pide DNU.
            query = select(Norma, DnuTracking.estado_bicameral).join(
                DnuTracking, DnuTracking.norma_id == Norma.id, isouter=True
            ).where(*filters).order_by(
                Norma.fecha_publicacion.desc().nullslast(), Norma.id.desc()
            ).limit(limit).offset(offset)
            rows = (await session.execute(query)).all()
            items = []
            for norma, estado_bicameral in rows:
                item = NormaListItem.model_validate(norma)
                item.estado_bicameral = estado_bicameral
                items.append(item)
        else:
            rows = (await session.execute(query)).scalars().all()
            items = [NormaListItem.model_validate(r) for r in rows]

    return NormaPage(items=items, total=int(total or 0), limit=limit, offset=offset)


@router.get("/{norma_id}", response_model=NormaDetail)
async def get_norma(norma_id: int) -> NormaDetail:
    Session = get_sessionmaker()
    async with Session() as session:
        row = (
            await session.execute(
                select(Norma, SourceCatalog.name, SourceCatalog.code)
                .join(SourceCatalog, SourceCatalog.id == Norma.source_id, isouter=True)
                .where(Norma.id == norma_id)
            )
        ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Norma no encontrada")
    norma, fuente, fuente_code = row
    detail = NormaDetail.model_validate(norma)
    detail.fuente = fuente
    detail.fuente_code = fuente_code
    if isinstance(norma.raw, dict):
        movs = norma.raw.get("movimientos")
        if isinstance(movs, list) and movs:
            detail.movimientos = movs
    return detail
