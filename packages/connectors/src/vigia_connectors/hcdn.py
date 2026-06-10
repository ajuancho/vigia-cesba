"""HCDN — proyectos parlamentarios (datos.hcdn.gob.ar, CKAN).

La Cámara de Diputados publica el dataset `proyectos-parlamentarios` con todos
los proyectos presentados (ley, resolución, declaración...), actualizado a
diario. Lo usamos como fuente del tipo `PROYECTO` del feed de Vigía.

La URL del recurso CSV cambia de nombre con cada versión (2.0, 2.2, ...), así
que se resuelve en runtime vía la API CKAN (`package_show`).

Columnas del CSV:
PROYECTO_ID, TITULO, PUBLICACION_FECHA, PUBLICACION_ID, CAMARA_ORIGEN,
EXP_DIPUTADOS, EXP_SENADO, TIPO, AUTOR
"""
from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from pathlib import Path
from typing import Self

from vigia_connectors._http import get_json, make_client
from vigia_connectors.sectores import detect_sector

CKAN_BASE = "https://datos.hcdn.gob.ar"
PACKAGE_ID = "proyectos-parlamentarios"


@dataclass(slots=True)
class HcdnProyecto:
    proyecto_id: str
    titulo: str
    fecha_publicacion: Date | None
    camara_origen: str | None
    exp_diputados: str | None
    exp_senado: str | None
    tipo_proyecto: str | None  # LEY | RESOLUCION | DECLARACION | ...
    autor: str | None

    @property
    def expediente(self) -> str | None:
        return self.exp_diputados or self.exp_senado

    def organismo(self) -> str:
        if (self.camara_origen or "").strip().lower().startswith("senado"):
            return "Honorable Senado de la Nación"
        return "Honorable Cámara de Diputados de la Nación"

    def detect_sector(self) -> str | None:
        return detect_sector(self.titulo)


def _parse_fecha(value: str | None) -> Date | None:
    value = (value or "").strip()
    if not value or value.upper() == "NA":
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "")).date()
    except ValueError:
        return None


def _na(value: str | None) -> str | None:
    v = (value or "").strip()
    return None if not v or v.upper() == "NA" else v


class HcdnClient:
    def __init__(self, *, timeout: float = 300.0) -> None:
        self._client = make_client(base_url=CKAN_BASE, timeout=timeout)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def resolve_csv_url(self, package_id: str = PACKAGE_ID) -> str:
        """Resuelve la URL vigente del recurso CSV de un package vía package_show.

        Las URLs de recursos cambian de nombre con cada versión (2.0, 3.5, ...),
        por eso siempre se resuelven en runtime.
        """
        data = await get_json(self._client, f"/api/3/action/package_show?id={package_id}")
        for res in data["result"]["resources"]:
            if (res.get("format") or "").upper() == "CSV":
                return res["url"]
        raise ValueError(f"No CSV resource in CKAN package {package_id}")

    async def download_csv(self, dest: Path, package_id: str = PACKAGE_ID) -> Path:
        """Stream del CSV completo de un package a disco."""
        url = await self.resolve_csv_url(package_id)
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with self._client.stream("GET", url) as resp:
            resp.raise_for_status()
            with dest.open("wb") as fh:
                async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                    if chunk:
                        fh.write(chunk)
        return dest

    @staticmethod
    def iter_csv(csv_path: Path) -> Iterator[HcdnProyecto]:
        """Itera proyectos de a uno desde el CSV en disco (memory-friendly)."""
        with csv_path.open("rb") as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.DictReader(text)
            for row in reader:
                p = HcdnClient._row_to_proyecto(row)
                if p is not None:
                    yield p

    @staticmethod
    def _row_to_proyecto(row: dict) -> "HcdnProyecto | None":
        try:
            pid = (row.get("PROYECTO_ID") or "").strip()
            titulo = (row.get("TITULO") or "").strip()
            if not pid or not titulo:
                return None
            return HcdnProyecto(
                proyecto_id=pid,
                titulo=titulo,
                fecha_publicacion=_parse_fecha(row.get("PUBLICACION_FECHA")),
                camara_origen=_na(row.get("CAMARA_ORIGEN")),
                exp_diputados=_na(row.get("EXP_DIPUTADOS")),
                exp_senado=_na(row.get("EXP_SENADO")),
                tipo_proyecto=_na(row.get("TIPO")),
                autor=_na(row.get("AUTOR")),
            )
        except Exception:
            return None
