"""Buscador full-text sobre `norma` (GIN sobre search_vector, español)."""
from __future__ import annotations

from datetime import date as Date

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import text

from vigia_api.core.db import get_sessionmaker

router = APIRouter(prefix="/search", tags=["search"])


class SearchHit(BaseModel):
    id: int
    tipo: str
    numero: str | None
    titulo: str
    resumen: str | None
    snippet: str | None
    fecha_publicacion: Date | None
    sector: str | None
    emisor: str | None
    organismo: str | None
    tags: list[str] | None
    rank: float | None


class SearchResponse(BaseModel):
    total: int
    query: str
    hits: list[SearchHit]


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query("", description="Texto libre (lenguaje natural)"),
    tipo: str | None = Query(None),
    sector: str | None = Query(None),
    emisor: str | None = Query(None, description="organismo canónico: ARCA|CNV|BCRA|…"),
    jurisdiccion: str | None = Query(None),
    limit: int = Query(40, ge=1, le=200),
    offset: int = Query(0, ge=0, le=10000),
) -> SearchResponse:
    Session = get_sessionmaker()
    has_q = bool(q.strip())

    where = []
    params: dict = {"limit": limit, "offset": offset}
    if has_q:
        where.append("search_vector @@ plainto_tsquery('spanish', :q)")
        params["q"] = q.strip()
    if tipo:
        where.append("tipo = :tipo")
        params["tipo"] = tipo
    if sector:
        where.append("sector = :sector")
        params["sector"] = sector
    if emisor:
        where.append("emisor = :emisor")
        params["emisor"] = emisor
    if jurisdiccion:
        where.append("jurisdiccion = :jur")
        params["jur"] = jurisdiccion

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rank_sql = (
        ", ts_rank_cd(search_vector, plainto_tsquery('spanish', :q)) AS rank"
        if has_q
        else ", NULL::float AS rank"
    )
    snippet_sql = (
        ", ts_headline('spanish', coalesce(resumen, titulo), plainto_tsquery('spanish', :q), "
        "'StartSel=«, StopSel=», MaxWords=35, MinWords=15, MaxFragments=1') AS snippet"
        if has_q
        else ", NULL::text AS snippet"
    )
    order_sql = (
        "ORDER BY rank DESC, fecha_publicacion DESC NULLS LAST"
        if has_q
        else "ORDER BY fecha_publicacion DESC NULLS LAST"
    )

    query_sql = f"""
        SELECT id, tipo, numero, titulo, resumen, fecha_publicacion, sector, organismo, tags, emisor
               {rank_sql}
               {snippet_sql}
        FROM norma
        {where_sql}
        {order_sql}
        LIMIT :limit OFFSET :offset
    """
    count_sql = f"SELECT COUNT(*) FROM norma {where_sql}"

    async with Session() as session:
        total = (await session.execute(text(count_sql), params)).scalar_one()
        rows = (await session.execute(text(query_sql), params)).all()

    hits = [
        SearchHit(
            id=r[0], tipo=r[1], numero=r[2], titulo=r[3], resumen=r[4],
            fecha_publicacion=r[5], sector=r[6], organismo=r[7], tags=r[8], emisor=r[9],
            rank=float(r[10]) if r[10] is not None else None,
            snippet=r[11],
        )
        for r in rows
    ]
    return SearchResponse(total=int(total or 0), query=q, hits=hits)
