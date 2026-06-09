"""Schemas Pydantic v2 compartidos (respuestas de API)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class NormaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    numero: str | None = None
    titulo: str
    resumen: str | None = None
    resumen_ia: str | None = None
    fecha_publicacion: date | None = None
    jurisdiccion: str | None = None
    sector: str | None = None
    organismo: str | None = None
    estado: str | None = None
    impacto: str | None = None
    bora_seccion: str | None = None
    tags: list[str] | None = None
    url: str | None = None


class NormaListItem(NormaBase):
    """Versión liviana para feed/búsqueda (sin entidades ni raw)."""


class NormaDetail(NormaBase):
    """Detalle completo de una norma."""

    entidades: list[str] | None = None
    ingested_at: datetime | None = None


class NormaPage(BaseModel):
    items: list[NormaListItem]
    total: int
    limit: int
    offset: int


class SectorStat(BaseModel):
    sector: str
    cantidad: int


class TipoStat(BaseModel):
    tipo: str
    cantidad: int


class DashboardStats(BaseModel):
    total_normas: int
    por_tipo: list[TipoStat]
    por_sector: list[SectorStat]


class DnuStats(BaseModel):
    total: int
    aprobados: int
    rechazados: int
    pendientes: int
