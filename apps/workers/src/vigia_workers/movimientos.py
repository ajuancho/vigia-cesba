"""Movimientos de proyectos HCDN → estado real de tramitación.

`ingest_hcdn_movimientos` NO crea normas: enriquece los PROYECTO existentes.
Baja el CSV de `movimientos-de-proyectos` (CKAN), agrupa por PROYECTO_ID
(== norma.external_id de hcdn_proyectos), deriva el estado de mayor rango
("Media sanción", "Sancionado", "Con dictamen", ...) y actualiza
`norma.estado` + guarda los últimos movimientos en `raw['movimientos']`
(timeline del detalle).

Gotcha de orden (documentado en CLAUDE/plan): `ingest_hcdn_proyectos` (08:00)
pisa `estado` con "En trámite" cada día — esta task corre DESPUÉS (08:30) y
recalcula todo, así el pisado se auto-repara diariamente.
"""
from __future__ import annotations

import json
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import text

from vigia_connectors import HcdnClient
from vigia_connectors.hcdn import MOVIMIENTOS_PACKAGE_ID, derivar_estado
from vigia_shared.db import session_scope
from vigia_workers.celery_app import celery_app
from vigia_workers.persistence import ensure_source, run_async, with_status

_TIMELINE_MAX = 8  # últimos movimientos que viajan al detalle

_UPDATE_SQL = """
UPDATE norma SET
    estado = :estado,
    raw = raw || jsonb_build_object('movimientos', CAST(:timeline AS jsonb))
WHERE external_id = :ext
  AND source_id = (SELECT id FROM source_catalog WHERE code = 'hcdn_proyectos')
  AND (estado IS DISTINCT FROM :estado OR raw->'movimientos' IS NULL
       OR raw->'movimientos' <> CAST(:timeline AS jsonb))
"""


async def _ingest(dry_run: bool = False) -> dict[str, Any]:
    por_proyecto: dict[str, list] = defaultdict(list)
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "movimientos.csv"
        async with HcdnClient() as client:
            await client.download_csv(dest, package_id=MOVIMIENTOS_PACKAGE_ID)
        for m in HcdnClient.iter_movimientos_csv(dest):
            por_proyecto[m.proyecto_id].append(m)

    actualizables: list[dict[str, Any]] = []
    estados_count: dict[str, int] = defaultdict(int)
    for pid, movs in por_proyecto.items():
        estado = derivar_estado([m.movimiento for m in movs])
        if estado is None:
            continue  # solo cofirmantes/mociones: sigue "En trámite"
        timeline = [
            {"movimiento": m.movimiento[:300], "fecha": m.fecha.isoformat() if m.fecha else None}
            for m in movs[-_TIMELINE_MAX:]
        ]
        estados_count[estado] += 1
        actualizables.append(
            {"ext": pid, "estado": estado, "timeline": json.dumps(timeline, ensure_ascii=False)}
        )

    if dry_run:
        return {
            "proyectos_con_movimientos": len(por_proyecto),
            "con_estado_derivado": len(actualizables),
            "estados": dict(estados_count),
        }

    async with session_scope() as session:
        # executemany por chunks: el WHERE evita reescribir filas sin cambios.
        # (asyncpg no reporta rowcount en executemany: no hay conteo fino.)
        for i in range(0, len(actualizables), 1000):
            chunk = actualizables[i : i + 1000]
            await session.execute(text(_UPDATE_SQL), chunk)

    return {
        "proyectos_con_movimientos": len(por_proyecto),
        "con_estado_derivado": len(actualizables),
        "estados": dict(estados_count),
    }


@celery_app.task(name="vigia_workers.movimientos.ingest_hcdn_movimientos")
def ingest_hcdn_movimientos(dry_run: bool = False) -> dict[str, Any]:
    import os

    dry = dry_run or os.environ.get("VIGIA_INGEST_DRY_RUN", "").strip().lower() in ("1", "true", "yes")
    if dry:
        result = run_async(_ingest(dry_run=True))
        return {"source": "hcdn_movimientos", "dry_run": True, **result}

    async def _wrapped() -> dict[str, Any]:
        await ensure_source("hcdn_movimientos")
        counts = await with_status(["hcdn_movimientos"], lambda: _ingest(dry_run=False))
        return {"source": "hcdn_movimientos", **counts}

    return run_async(_wrapped())
