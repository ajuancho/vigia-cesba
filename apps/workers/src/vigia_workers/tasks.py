"""Tasks de ingesta de Celery.

Cada task es idempotente (upsert por (source_id, external_id)). Se pueden
invocar desde CLI:

    python -c "from vigia_workers.tasks import ingest_infoleg as t; print(t())"

…o agendar por celery-beat (ver celery_app.py).

Dry-run (no escribe en la DB; fetch + parse + conteos + sample de filas):

    python -c "from vigia_workers.tasks import ingest_infoleg as t; print(t(dry_run=True))"

…o exportando VIGIA_INGEST_DRY_RUN=1 (aplica a todas las tasks de ingesta).
"""
from __future__ import annotations

import dataclasses
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from vigia_connectors import BoraAviso, BoraClient, HcdnClient, HcdnProyecto, InfoLegClient, InfoLegNorm
from vigia_connectors.bora import looks_like_dnu
from vigia_shared.sources import catalog_fields
from vigia_workers.celery_app import celery_app
from vigia_workers.persistence import mark_source_run, run_async, upsert_normas, with_status

INFOLEG_SOURCE = catalog_fields("infoleg")
HCDN_SOURCE = catalog_fields("hcdn_proyectos")
BORA_SOURCE = catalog_fields("bora_primera")

# Cuántos registros por batch al persistir el corpus completo.
# Tope: asyncpg admite máx 32767 parámetros bind por statement
# (~17 columnas por fila → 1000 filas ≈ 17k params, margen cómodo).
_FULL_BATCH = 1000

# Cuántas filas de muestra reporta un dry-run.
_DRY_SAMPLE = 5


def _is_dry_run(flag: bool) -> bool:
    return flag or os.environ.get("VIGIA_INGEST_DRY_RUN", "").strip().lower() in ("1", "true", "yes")


def _dry_sample_row(row: dict[str, Any]) -> dict[str, Any]:
    """Versión legible de una fila para el reporte de dry-run (sin raw)."""
    keep = ("external_id", "tipo", "numero", "titulo", "fecha_publicacion", "organismo", "sector")
    out = {k: row.get(k) for k in keep}
    if isinstance(out.get("fecha_publicacion"), date):
        out["fecha_publicacion"] = out["fecha_publicacion"].isoformat()
    return out


def _empty_totals() -> dict[str, int]:
    return {"rows": 0, "inserted": 0, "updated": 0}


def _acc(totals: dict[str, int], part: dict[str, int]) -> None:
    for k in ("rows", "inserted", "updated"):
        totals[k] += part[k]


def _norma_to_row(n: InfoLegNorm) -> dict[str, Any]:
    """Mapea un InfoLegNorm al shape de la tabla `norma`."""
    titulo = n.titulo_resumido or n.titulo_sumario or f"{n.tipo_norma} {n.numero_norma or ''}".strip()
    resumen = n.texto_resumido or n.titulo_sumario
    fecha = n.fecha_boletin or n.fecha_sancion
    return {
        "external_id": n.id_norma,
        "tipo": n.tipo_slug(),
        "numero": n.numero_norma,
        "titulo": titulo,
        "resumen": resumen,
        "fecha_publicacion": fecha,
        "jurisdiccion": "Nacional",
        "sector": n.detect_sector(),
        "organismo": n.organismo_origen,
        "estado": "Publicada" if n.fecha_boletin else None,
        "impacto": None,  # heurística de impacto -> fase posterior
        "bora_seccion": "Primera Sección" if n.numero_boletin else None,
        "entidades": None,  # NER -> Fase 5
        "tags": None,
        "url": n.texto_original_url,
        "raw": {k: (v.isoformat() if isinstance(v, date) else v)
                for k, v in dataclasses.asdict(n).items()},
    }


@celery_app.task(name="vigia_workers.tasks.ingest_infoleg")
def ingest_infoleg(dry_run: bool = False) -> dict[str, Any]:
    """Ingesta el muestreo de InfoLEG (~1000 normas). Rápido — bueno para dev."""
    dry = _is_dry_run(dry_run)

    async def _run() -> dict[str, Any]:
        async with InfoLegClient() as client:
            normas = await client.fetch_sample()
        rows = [_norma_to_row(n) for n in normas]
        if dry:
            return {"rows": len(rows), "sample": [_dry_sample_row(r) for r in rows[:_DRY_SAMPLE]]}
        return await upsert_normas(INFOLEG_SOURCE, rows)

    if dry:
        result = run_async(_run())
        return {"source": "infoleg", "mode": "sample", "dry_run": True, **result}

    async def _wrapped() -> dict[str, Any]:
        counts = await with_status([INFOLEG_SOURCE["code"]], _run)
        return {"source": "infoleg", "mode": "sample", **counts}

    result = run_async(_wrapped())
    # Tras ingestar, cruzar contra las alertas activas y notificar.
    from vigia_workers.alerts import _match_all
    result["matching"] = run_async(_match_all())
    return result


def _proyecto_to_row(p: HcdnProyecto) -> dict[str, Any]:
    """Mapea un HcdnProyecto al shape de la tabla `norma` (tipo PROYECTO)."""
    return {
        "external_id": p.proyecto_id,
        "tipo": "PROYECTO",
        "numero": p.expediente,
        "titulo": p.titulo,
        "resumen": None,
        "fecha_publicacion": p.fecha_publicacion,
        "jurisdiccion": "Nacional",
        "sector": p.detect_sector(),
        "organismo": p.organismo(),
        "estado": "En trámite",
        "impacto": None,
        "bora_seccion": None,
        "entidades": [p.autor] if p.autor else None,
        "tags": [p.tipo_proyecto.lower()] if p.tipo_proyecto else None,
        "url": None,
        "raw": {k: (v.isoformat() if isinstance(v, date) else v)
                for k, v in dataclasses.asdict(p).items()},
    }


@celery_app.task(name="vigia_workers.tasks.ingest_hcdn_proyectos")
def ingest_hcdn_proyectos(dry_run: bool = False) -> dict[str, Any]:
    """Ingesta los proyectos parlamentarios de HCDN (CSV completo por streaming).

    El dataset se actualiza a diario en datos.hcdn.gob.ar; el upsert es
    idempotente por (source_id, external_id=PROYECTO_ID).
    """
    dry = _is_dry_run(dry_run)

    async def _run() -> dict[str, Any]:
        totals = _empty_totals()
        sample: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "proyectos.csv"
            async with HcdnClient() as client:
                await client.download_csv(dest)
            batch: list[dict[str, Any]] = []
            for p in HcdnClient.iter_csv(dest):
                row = _proyecto_to_row(p)
                if dry:
                    totals["rows"] += 1
                    if len(sample) < _DRY_SAMPLE:
                        sample.append(_dry_sample_row(row))
                    continue
                batch.append(row)
                if len(batch) >= _FULL_BATCH:
                    _acc(totals, await upsert_normas(HCDN_SOURCE, batch))
                    batch = []
            if batch:
                _acc(totals, await upsert_normas(HCDN_SOURCE, batch))
        if dry:
            return {"rows": totals["rows"], "sample": sample}
        return totals

    if dry:
        result = run_async(_run())
        return {"source": "hcdn_proyectos", "dry_run": True, **result}

    async def _wrapped() -> dict[str, Any]:
        counts = await with_status([HCDN_SOURCE["code"]], _run)
        return {"source": "hcdn_proyectos", **counts}

    return run_async(_wrapped())


def _aviso_to_row(a: BoraAviso, tipo: str | None = None) -> dict[str, Any]:
    """Mapea un BoraAviso (1ª sección) al shape de la tabla `norma`."""
    titulo = a.sumario or a.tipo_linea or f"Aviso {a.aviso_id}"
    return {
        "external_id": a.aviso_id,
        "tipo": tipo or a.tipo_slug(),
        "numero": a.numero,
        "titulo": titulo,
        "resumen": a.sumario,
        "fecha_publicacion": a.fecha,
        "jurisdiccion": "Nacional",
        "sector": a.detect_sector(),
        "organismo": a.organismo,
        "estado": "Publicada",
        "impacto": None,
        "bora_seccion": "Primera Sección",
        "entidades": None,
        "tags": None,
        "url": a.url,
        "raw": {k: (v.isoformat() if isinstance(v, date) else v)
                for k, v in dataclasses.asdict(a).items()},
    }


@celery_app.task(name="vigia_workers.tasks.ingest_bora_primera")
def ingest_bora_primera(dry_run: bool = False, lookback_days: int = 5) -> dict[str, Any]:
    """Ingesta la 1ª sección del BORA (edición del día + lookback de catch-up).

    El lookback re-scrapea los últimos N días: idempotente (upsert) y
    auto-recupera outages sin task manual. Los DNU salen del BO como
    "Decreto" — se promueven mirando el texto del detalle (art. 99 inc. 3);
    si la heurística falla, InfoLEG corrige al alcanzar (~2 semanas).
    """
    import asyncio as _asyncio
    from datetime import timedelta

    dry = _is_dry_run(dry_run)
    hoy = date.today()
    fechas = [hoy - timedelta(days=d) for d in range(lookback_days)]

    async def _run() -> dict[str, Any]:
        totals = _empty_totals()
        sample: list[dict[str, Any]] = []
        avisos_hoy = 0
        async with BoraClient() as client:
            for fecha in fechas:
                avisos = await client.fetch_seccion("primera", fecha)
                if fecha == hoy:
                    avisos_hoy = len(avisos)
                if not avisos:
                    continue
                # Detección de DNU: solo para decretos (pocos por día).
                decretos = [a for a in avisos if a.tipo_slug() == "DECRETO"]
                textos = await _asyncio.gather(
                    *(client.fetch_detalle_texto(a) for a in decretos),
                    return_exceptions=True,
                )
                es_dnu = {
                    a.aviso_id
                    for a, t in zip(decretos, textos)
                    if not isinstance(t, Exception) and looks_like_dnu(t)
                }
                rows = [
                    _aviso_to_row(a, tipo="DNU" if a.aviso_id in es_dnu else None)
                    for a in avisos
                ]
                if dry:
                    totals["rows"] += len(rows)
                    sample.extend(_dry_sample_row(r) for r in rows[: max(0, _DRY_SAMPLE - len(sample))])
                    continue
                _acc(totals, await upsert_normas(BORA_SOURCE, rows))
        if dry:
            return {"rows": totals["rows"], "sample": sample, "avisos_hoy": avisos_hoy}
        return {**totals, "avisos_hoy": avisos_hoy}

    if dry:
        result = run_async(_run())
        return {"source": "bora_primera", "dry_run": True, **result}

    async def _wrapped() -> dict[str, Any]:
        counts = await with_status([BORA_SOURCE["code"]], _run)
        return {"source": "bora_primera", **counts}

    result = run_async(_wrapped())

    # Guard: día hábil sin avisos = probable cambio de HTML (el parser devolvió
    # vacío sin error). Queda visible en /health/sources.
    if result.get("avisos_hoy", 0) == 0 and hoy.weekday() < 5:
        run_async(
            mark_source_run(
                BORA_SOURCE["code"],
                status="warn",
                error="0 avisos en día hábil — ¿feriado o cambió el HTML del listado?",
            )
        )

    # Dedup contra InfoLEG + matching de alertas (frescura inmediata).
    from vigia_workers.reconcile import _reconcile
    result["reconcile"] = run_async(_reconcile())
    from vigia_workers.alerts import _match_all
    result["matching"] = run_async(_match_all())
    return result


@celery_app.task(name="vigia_workers.tasks.ingest_infoleg_full")
def ingest_infoleg_full(dry_run: bool = False) -> dict[str, Any]:
    """Ingesta el corpus completo de InfoLEG (~500k normas) por streaming.

    Descarga el ZIP a un temp file y persiste en batches para no cargar todo
    en memoria.
    """
    dry = _is_dry_run(dry_run)

    async def _run() -> dict[str, Any]:
        totals = _empty_totals()
        sample: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "infoleg_full.zip"
            async with InfoLegClient() as client:
                await client.download_full_zip(dest)
            batch: list[dict[str, Any]] = []
            for norm in InfoLegClient.iter_full_zip(dest):
                row = _norma_to_row(norm)
                if dry:
                    totals["rows"] += 1
                    if len(sample) < _DRY_SAMPLE:
                        sample.append(_dry_sample_row(row))
                    continue
                batch.append(row)
                if len(batch) >= _FULL_BATCH:
                    _acc(totals, await upsert_normas(INFOLEG_SOURCE, batch))
                    batch = []
            if batch:
                _acc(totals, await upsert_normas(INFOLEG_SOURCE, batch))
        if dry:
            return {"rows": totals["rows"], "sample": sample}
        return totals

    if dry:
        result = run_async(_run())
        return {"source": "infoleg", "mode": "full", "dry_run": True, **result}

    async def _wrapped() -> dict[str, Any]:
        counts = await with_status([INFOLEG_SOURCE["code"]], _run)
        return {"source": "infoleg", "mode": "full", **counts}

    return run_async(_wrapped())
