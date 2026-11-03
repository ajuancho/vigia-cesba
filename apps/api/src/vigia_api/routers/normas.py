"""Feed de normas + detalle. Lee de Postgres (poblado por el worker InfoLEG)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, select

from vigia_api.core.db import get_sessionmaker
from vigia_api.core.scope import norma_filters
from vigia_shared.models import DnuTracking, Norma, SourceCatalog
from vigia_shared.fuentes import SECCION_LEGISLATURA
from vigia_shared.relevancia import PESO_TIPO, es_tramite
from vigia_shared.schemas import NormaDetail, NormaListItem, NormaPage

router = APIRouter(prefix="/normas", tags=["normas"])

# Topes por edición (el cliente muestra lo que llega; el resto queda contado).
_MAX_DESTACADOS = 30
_MAX_TRAMITE = 80


@router.get("/ediciones")
async def ediciones(
    dias: int = Query(7, ge=1, le=31, description="cuántas ediciones (días con normas) traer"),
    offset_dias: int = Query(0, ge=0, le=365, description="paginación: saltear N ediciones"),
    tipo: str | None = Query(None),
    sector: str | None = Query(None),
    emisor: str | None = Query(None, description="organismo canónico: ARCA|CNV|BCRA|…"),
) -> dict:
    """El feed como diario: una edición por día, con jerarquía editorial.

    Cada edición separa `destacados` (DNU, leyes, decretos de alcance general,
    normativa regulatoria) de `tramite` (edictos, designaciones, beneplácitos),
    que el cliente colapsa en una línea. Orden: peso editorial del tipo.
    Los expedientes de la Legislatura no son parte del Boletín: tienen su
    propia vista (`GET /normas?seccion=Legislatura`).
    """
    Session = get_sessionmaker()
    filters = norma_filters()
    filters.append(or_(Norma.bora_seccion.is_(None), Norma.bora_seccion != SECCION_LEGISLATURA))
    if tipo:
        filters.append(Norma.tipo == tipo)
    if sector:
        filters.append(Norma.sector == sector)
    if emisor:
        filters.append(Norma.emisor == emisor)

    async with Session() as session:
        fechas = (
            await session.execute(
                select(Norma.fecha_publicacion)
                .where(Norma.fecha_publicacion.isnot(None), *filters)
                .group_by(Norma.fecha_publicacion)
                .order_by(Norma.fecha_publicacion.desc())
                .limit(dias + 1)  # +1 para saber si hay más
                .offset(offset_dias)
            )
        ).scalars().all()
        has_more = len(fechas) > dias
        fechas = fechas[:dias]
        if not fechas:
            return {"ediciones": [], "has_more": False}

        rows = (
            await session.execute(
                select(Norma)
                .where(Norma.fecha_publicacion.in_(fechas), *filters)
                .order_by(Norma.fecha_publicacion.desc(), Norma.id.desc())
            )
        ).scalars().all()

    por_fecha: dict = {f: {"destacados": [], "tramite": []} for f in fechas}
    resumen: dict = {f: {} for f in fechas}
    for n in rows:
        raw = n.raw if isinstance(n.raw, dict) else {}
        bucket = (
            "tramite"
            if es_tramite(n.tipo, n.titulo, tags=n.tags, tipo_linea=raw.get("tipo_linea"))
            else "destacados"
        )
        por_fecha[n.fecha_publicacion][bucket].append(n)
        r = resumen[n.fecha_publicacion]
        r[n.tipo] = r.get(n.tipo, 0) + 1

    out = []
    for f in fechas:
        destacados = sorted(
            por_fecha[f]["destacados"], key=lambda n: (PESO_TIPO.get(n.tipo, 9), -n.id)
        )
        tramite = por_fecha[f]["tramite"]
        out.append(
            {
                "fecha": f.isoformat(),
                "resumen": resumen[f],
                "destacados_total": len(destacados),
                "tramite_total": len(tramite),
                "destacados": [
                    NormaListItem.model_validate(n) for n in destacados[:_MAX_DESTACADOS]
                ],
                "tramite": [NormaListItem.model_validate(n) for n in tramite[:_MAX_TRAMITE]],
            }
        )
    return {"ediciones": out, "has_more": has_more}


@router.get("", response_model=NormaPage)
async def list_normas(
    tipo: str | None = Query(None, description="DNU|DECRETO|LEY|RESOLUCION|DISPOSICION|PROYECTO|COMUNICACION|OTRA"),
    impacto: str | None = Query(None, description="alto|medio|bajo"),
    sector: str | None = Query(None),
    emisor: str | None = Query(None, description="organismo canónico: ARCA|CNV|BCRA|…"),
    seccion: str | None = Query(None, description="sección de origen: 'Licitaciones', 'Legislatura', …"),
    tipo_nombre: str | None = Query(None, description="tipo tal como lo publica la fuente: 'Proyecto de ley', …"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
) -> NormaPage:
    Session = get_sessionmaker()
    filters = norma_filters()
    if tipo:
        filters.append(Norma.tipo == tipo)
    if impacto:
        filters.append(Norma.impacto == impacto)
    if sector:
        filters.append(Norma.sector == sector)
    if emisor:
        filters.append(Norma.emisor == emisor)
    if seccion:
        filters.append(Norma.bora_seccion == seccion)
    if tipo_nombre:
        filters.append(Norma.raw["tipo_nombre"].astext == tipo_nombre)

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
            items = []
            for r in rows:
                item = NormaListItem.model_validate(r)
                item.tipo_nombre = (r.raw or {}).get("tipo_nombre")
                items.append(item)

    return NormaPage(items=items, total=int(total or 0), limit=limit, offset=offset)


@router.get("/{norma_id}", response_model=NormaDetail)
async def get_norma(norma_id: int) -> NormaDetail:
    Session = get_sessionmaker()
    async with Session() as session:
        row = (
            await session.execute(
                select(Norma, SourceCatalog.name, SourceCatalog.code)
                .join(SourceCatalog, SourceCatalog.id == Norma.source_id, isouter=True)
                .where(Norma.id == norma_id, *norma_filters())
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
