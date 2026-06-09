"""Alertas de monitoreo (JWT requerido). Persistidas por workspace.

El matching norma↔alerta lo hace el worker (`vigia_workers.alerts`); acá sólo
se gestionan las suscripciones y se leen los matches.
"""
from __future__ import annotations

from datetime import date as Date
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, func, select, update

from vigia_api.core.db import get_sessionmaker
from vigia_api.core.security import WorkspaceContext, current_workspace
from vigia_shared.models import Alerta, AlertaMatch, Norma

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _require_real_workspace(ctx: WorkspaceContext) -> None:
    if ctx.workspace_id == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="auth_required_for_alerts",
        )


class AlertaIn(BaseModel):
    keyword: str
    sector: str | None = None


class AlertaPatch(BaseModel):
    activa: bool


class AlertaOut(BaseModel):
    id: int
    keyword: str
    sector: str | None
    activa: bool
    matches: int
    last_match_at: datetime | None


class MatchOut(BaseModel):
    norma_id: int
    tipo: str
    numero: str | None
    titulo: str
    fecha_publicacion: Date | None
    matched_at: datetime


@router.get("", response_model=list[AlertaOut])
async def list_alertas(ctx: Annotated[WorkspaceContext, Depends(current_workspace)]) -> list[AlertaOut]:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(
                select(Alerta, func.count(AlertaMatch.id))
                .outerjoin(AlertaMatch, AlertaMatch.alerta_id == Alerta.id)
                .where(Alerta.workspace_id == ctx.workspace_id)
                .group_by(Alerta.id)
                .order_by(Alerta.created_at.desc())
            )
        ).all()
    return [
        AlertaOut(
            id=a.id, keyword=a.keyword, sector=a.sector, activa=a.activa,
            matches=int(c or 0), last_match_at=a.last_match_at,
        )
        for a, c in rows
    ]


@router.post("", response_model=AlertaOut, status_code=201)
async def create_alerta(
    body: AlertaIn,
    ctx: Annotated[WorkspaceContext, Depends(current_workspace)],
) -> AlertaOut:
    _require_real_workspace(ctx)
    if not body.keyword.strip():
        raise HTTPException(422, "keyword_required")
    Session = get_sessionmaker()
    async with Session() as session:
        a = Alerta(
            workspace_id=ctx.workspace_id,
            user_id=ctx.user_id or None,
            keyword=body.keyword.strip(),
            sector=body.sector or None,
            activa=True,
        )
        session.add(a)
        await session.commit()
        await session.refresh(a)
    return AlertaOut(id=a.id, keyword=a.keyword, sector=a.sector, activa=a.activa, matches=0, last_match_at=None)


@router.patch("/{alerta_id}", response_model=AlertaOut)
async def toggle_alerta(
    alerta_id: int,
    body: AlertaPatch,
    ctx: Annotated[WorkspaceContext, Depends(current_workspace)],
) -> AlertaOut:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        a = await session.scalar(
            select(Alerta).where(Alerta.id == alerta_id, Alerta.workspace_id == ctx.workspace_id)
        )
        if a is None:
            raise HTTPException(404, "alerta_not_found")
        a.activa = body.activa
        await session.commit()
        count = await session.scalar(
            select(func.count()).select_from(AlertaMatch).where(AlertaMatch.alerta_id == a.id)
        )
    return AlertaOut(
        id=a.id, keyword=a.keyword, sector=a.sector, activa=a.activa,
        matches=int(count or 0), last_match_at=a.last_match_at,
    )


@router.delete("/{alerta_id}", status_code=204)
async def delete_alerta(
    alerta_id: int,
    ctx: Annotated[WorkspaceContext, Depends(current_workspace)],
) -> None:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        res = await session.execute(
            delete(Alerta).where(Alerta.id == alerta_id, Alerta.workspace_id == ctx.workspace_id)
        )
        if res.rowcount == 0:
            raise HTTPException(404, "alerta_not_found")
        await session.commit()


@router.get("/{alerta_id}/matches", response_model=list[MatchOut])
async def alerta_matches(
    alerta_id: int,
    ctx: Annotated[WorkspaceContext, Depends(current_workspace)],
) -> list[MatchOut]:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        owns = await session.scalar(
            select(Alerta.id).where(Alerta.id == alerta_id, Alerta.workspace_id == ctx.workspace_id)
        )
        if owns is None:
            raise HTTPException(404, "alerta_not_found")
        rows = (
            await session.execute(
                select(AlertaMatch, Norma)
                .join(Norma, Norma.id == AlertaMatch.norma_id)
                .where(AlertaMatch.alerta_id == alerta_id)
                .order_by(AlertaMatch.matched_at.desc())
                .limit(50)
            )
        ).all()
    return [
        MatchOut(
            norma_id=n.id, tipo=n.tipo, numero=n.numero, titulo=n.titulo,
            fecha_publicacion=n.fecha_publicacion, matched_at=m.matched_at,
        )
        for m, n in rows
    ]
