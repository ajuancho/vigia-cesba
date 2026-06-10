"""Reconciliación BORA ↔ InfoLEG: dedup cross-source de la misma norma.

BORA publica la norma el día D; InfoLEG la trae ~2 semanas después con otro
(source_id, external_id) → dos filas para la misma norma (feed duplicado y
doble notificación de alertas). InfoLEG es el corpus canónico (permalink
estable, clase_norma, referencias), así que cuando llega la gemela:

1. Se trasplantan los matches de alertas de la fila BORA a la InfoLEG con
   notified=true (la fila InfoLEG NO re-notifica lo ya avisado vía BORA).
2. Se copia el dnu_tracking más avanzado si difiere.
3. Se borra la fila BORA (CASCADE limpia sus matches/tracking).

Clave natural restringida a tipos de numeración nacional no ambigua, siempre
con igualdad de fecha_publicacion (misma edición del BO):
- LEY: número.
- DECRETO/DNU (familia única: los DNU comparten secuencia con los decretos y
  las fuentes pueden clasificarlos distinto): número + guard del instrumento
  ("Decreto..." vs "Decisión Administrativa...", que numeran por separado).
RESOLUCION/DISPOSICION quedan para una fase 2 (mismo número en N organismos
el mismo día — preferimos dup visible a falso merge).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text

from vigia_shared.db import session_scope
from vigia_workers.celery_app import celery_app
from vigia_workers.persistence import run_async

# int inicial del campo numero ("436/2026" -> 436, "27804" -> 27804).
_NUMINT = "NULLIF(regexp_replace(split_part(COALESCE({col}, ''), '/', 1), '[^0-9]', '', 'g'), '')::bigint"

_PAIRS_SQL = f"""
SELECT b.id AS dup_id, i.id AS canon_id
FROM norma b
JOIN norma i
  ON i.source_id = :infoleg_id
 AND i.fecha_publicacion = b.fecha_publicacion
 AND {_NUMINT.format(col="i.numero")} = {_NUMINT.format(col="b.numero")}
 AND (
       (b.tipo = 'LEY' AND i.tipo = 'LEY')
    OR (
        b.tipo IN ('DECRETO', 'DNU') AND i.tipo IN ('DECRETO', 'DNU')
        -- "Decreto" y "Decisión Administrativa" mapean ambos a DECRETO pero
        -- numeran por separado: exigir el mismo instrumento de origen.
        AND lower(substr(COALESCE(b.raw->>'tipo_linea', ''), 1, 6))
            = lower(substr(COALESCE(i.raw->>'tipo_norma', ''), 1, 6))
    )
 )
WHERE b.source_id = :bora_id
  AND b.numero IS NOT NULL
"""

_ORPHANS_SQL = """
SELECT COUNT(*) FROM norma b
WHERE b.source_id = :bora_id
  AND b.tipo IN ('LEY', 'DECRETO', 'DNU')
  AND b.fecha_publicacion < CURRENT_DATE - INTERVAL '30 days'
"""


async def _source_id(session, code: str) -> int | None:
    return await session.scalar(
        text("SELECT id FROM source_catalog WHERE code = :code"), {"code": code}
    )


async def _reconcile(bora_code: str = "bora_primera", infoleg_code: str = "infoleg") -> dict[str, Any]:
    async with session_scope() as session:
        bora_id = await _source_id(session, bora_code)
        infoleg_id = await _source_id(session, infoleg_code)
        if bora_id is None or infoleg_id is None:
            return {"merged": 0, "skipped": "fuente sin filas todavía"}

        params = {"bora_id": bora_id, "infoleg_id": infoleg_id}
        pairs = (await session.execute(text(_PAIRS_SQL), params)).all()

        for dup_id, canon_id in pairs:
            # 1. Anti doble-notificación: la fila InfoLEG hereda los matches
            #    ya notificados de la fila BORA.
            await session.execute(
                text(
                    """
                    INSERT INTO alerta_match (alerta_id, norma_id, notified)
                    SELECT alerta_id, :canon_id, true
                    FROM alerta_match WHERE norma_id = :dup_id
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"dup_id": dup_id, "canon_id": canon_id},
            )
            # 2. Conservar el tracking de DNU más avanzado.
            await session.execute(
                text(
                    """
                    UPDATE dnu_tracking c
                    SET estado_bicameral = d.estado_bicameral,
                        fecha_dictamen = d.fecha_dictamen,
                        notas = d.notas
                    FROM dnu_tracking d
                    WHERE d.norma_id = :dup_id
                      AND c.norma_id = :canon_id
                      AND c.estado_bicameral = 'pendiente'
                      AND d.estado_bicameral <> 'pendiente'
                    """
                ),
                {"dup_id": dup_id, "canon_id": canon_id},
            )
            # 3. La fila BORA se va (CASCADE limpia matches y tracking propios).
            await session.execute(text("DELETE FROM norma WHERE id = :dup_id"), {"dup_id": dup_id})

        # Señal de salud del dedup: filas BORA viejas que InfoLEG nunca cubrió
        # (parser de número roto o cobertura InfoLEG caída).
        orphans = await session.scalar(text(_ORPHANS_SQL), {"bora_id": bora_id})

    result = {"merged": len(pairs), "bora_huerfanas_30d": int(orphans or 0)}
    if pairs:
        print(f"[reconcile] {len(pairs)} filas BORA reemplazadas por sus gemelas InfoLEG")
    if orphans:
        print(f"[reconcile] WARN: {orphans} filas BORA LEY/DECRETO/DNU >30d sin gemela InfoLEG")
    return result


@celery_app.task(name="vigia_workers.reconcile.reconcile_bora_infoleg")
def reconcile_bora_infoleg() -> dict[str, Any]:
    return run_async(_reconcile())
