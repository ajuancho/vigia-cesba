"""Tracking bicameral de DNU: de dictámenes HCDN a `dnu_tracking`.

`ingest_bicameral_dnu` NO crea normas — actualiza estados de DNU existentes:

1. Baja el CSV de dictámenes de HCDN (CKAN) y filtra los de la Comisión
   Bicameral Permanente de Trámite Legislativo (ley 26.122).
2. Resuelve el DNU de cada dictamen: EXPEDIENTE → proyecto ya ingestado
   (norma.external_id de hcdn_proyectos) → número/año del DNU en su título.
3. UPDATE dnu_tracking → estado "dictaminado" + fecha + sentido en notas.
   ("aprobado"/"rechazado" requieren resolución de AMBAS cámaras — art. 24
   ley 26.122 — y se cargan manualmente hasta tener fuente de votaciones.)
4. Idempotente extra: los DNU previos a la ley 26.122 (jul-2006) pasan de
   "pendiente" a "sin_tratamiento" — nunca van a tener dictamen y inflaban
   el tracker (1187 "pendientes").

Los dictámenes sin match se loguean y cuentan; la task nunca falla por eso.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy import text

from vigia_connectors import HcdnClient
from vigia_connectors.bicameral import (
    DICTAMENES_PACKAGE_ID,
    iter_dictamenes_bicameral,
    parse_dnu_ref,
)
from vigia_shared.db import session_scope
from vigia_workers.celery_app import celery_app
from vigia_workers.persistence import ensure_source, run_async, with_status

# La ley 26.122 (que crea la Bicameral) se promulgó el 27-jul-2006.
_LEY_26122 = "2006-07-28"

_FIND_DNU_SQL = """
SELECT n.id FROM norma n
WHERE n.tipo = 'DNU'
  AND NULLIF(regexp_replace(split_part(COALESCE(n.numero, ''), '/', 1), '[^0-9]', '', 'g'), '')::bigint = :numero
  AND (
        CAST(:anio AS integer) IS NULL
     OR EXTRACT(YEAR FROM n.fecha_publicacion) = CAST(:anio AS integer)
     OR (n.raw->>'fecha_sancion') LIKE :anio_prefix
  )
"""

_UPDATE_TRACKING_SQL = """
UPDATE dnu_tracking
SET estado_bicameral = 'dictaminado',
    fecha_dictamen = COALESCE(:fecha, fecha_dictamen),
    notas = :notas,
    raw = :raw
WHERE norma_id = :norma_id
  AND estado_bicameral IN ('pendiente', 'sin_tratamiento', 'dictaminado')
"""

_SIN_TRATAMIENTO_SQL = f"""
UPDATE dnu_tracking t
SET estado_bicameral = 'sin_tratamiento'
FROM norma n
WHERE n.id = t.norma_id
  AND t.estado_bicameral = 'pendiente'
  AND n.fecha_publicacion < '{_LEY_26122}'
"""


async def _ingest(dry_run: bool = False) -> dict[str, Any]:
    import json

    dictaminados = 0
    sin_match: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "dictamenes.csv"
        async with HcdnClient() as client:
            await client.download_csv(dest, package_id=DICTAMENES_PACKAGE_ID)
        dictamenes = list(iter_dictamenes_bicameral(dest))

    async with session_scope() as session:
        for d in dictamenes:
            # 1) Número/año del DNU desde el título del proyecto de comunicación
            #    (ya ingestado a diario); fallback: las observaciones del dictamen.
            titulo = await session.scalar(
                text(
                    "SELECT n.titulo FROM norma n "
                    "JOIN source_catalog s ON s.id = n.source_id "
                    "WHERE s.code = 'hcdn_proyectos' AND n.external_id = :ext"
                ),
                {"ext": d.expediente_hcdn},
            )
            ref = parse_dnu_ref(titulo) or parse_dnu_ref(d.observaciones)
            if ref is None:
                sin_match.append(f"{d.expediente_hcdn}: sin referencia a DNU")
                continue
            numero, anio = ref
            if anio is None:
                # Sin año el match por número solo es ambiguo (el DNU 73 existe
                # en varios años): preferimos no actualizar a actualizar mal.
                sin_match.append(f"{d.expediente_hcdn}: DNU {numero} sin año — ambiguo")
                continue

            # 2) DNU(s) en el corpus (puede haber fila BORA + InfoLEG hasta el
            #    reconcile: se actualizan ambas).
            dnu_ids = (
                await session.execute(
                    text(_FIND_DNU_SQL),
                    {"numero": numero, "anio": anio, "anio_prefix": f"{anio}-%"},
                )
            ).scalars().all()
            if not dnu_ids:
                sin_match.append(f"{d.expediente_hcdn}: DNU {numero}/{anio} no está en el corpus")
                continue

            sentido = d.veredicto()
            notas = f"Dictamen de mayoría: {sentido or 'sin sentido claro'}"
            if d.observaciones:
                notas += f" — {d.observaciones[:400]}"
            if dry_run:
                dictaminados += len(dnu_ids)
                continue
            for norma_id in dnu_ids:
                await session.execute(
                    text(_UPDATE_TRACKING_SQL),
                    {
                        "norma_id": norma_id,
                        "fecha": d.fecha,
                        "notas": notas,
                        "raw": json.dumps(
                            {
                                "expediente": d.expediente_hcdn,
                                "numero_od": d.numero_od,
                                "fecha": d.fecha.isoformat() if d.fecha else None,
                                "veredicto": sentido,
                                "observaciones": d.observaciones,
                            }
                        ),
                    },
                )
                dictaminados += 1

        # 3) DNU pre-ley 26.122: nunca van a tener dictamen.
        sin_tratamiento = 0
        if not dry_run:
            res = await session.execute(text(_SIN_TRATAMIENTO_SQL))
            sin_tratamiento = res.rowcount or 0

    if sin_match:
        print(f"[bicameral] {len(sin_match)} dictámenes sin match (primeros 5): {sin_match[:5]}")
    return {
        "dictamenes": len(dictamenes),
        "dictaminados": dictaminados,
        "sin_match": len(sin_match),
        "sin_tratamiento_marcados": sin_tratamiento,
    }


@celery_app.task(name="vigia_workers.bicameral.ingest_bicameral_dnu")
def ingest_bicameral_dnu(dry_run: bool = False) -> dict[str, Any]:
    import os

    dry = dry_run or os.environ.get("VIGIA_INGEST_DRY_RUN", "").strip().lower() in ("1", "true", "yes")
    if dry:
        result = run_async(_ingest(dry_run=True))
        return {"source": "bicameral_dnu", "dry_run": True, **result}

    async def _wrapped() -> dict[str, Any]:
        await ensure_source("bicameral_dnu")
        counts = await with_status(["bicameral_dnu"], lambda: _ingest(dry_run=False))
        return {"source": "bicameral_dnu", **counts}

    return run_async(_wrapped())
