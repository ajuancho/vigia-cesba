"""Tasks de ingesta de Celery.

Cada task es idempotente (upsert por (source_id, external_id)). Se pueden
invocar desde CLI:

    python -c "from vigia_workers.tasks import ingest_infoleg as t; print(t())"

…o agendar por celery-beat (ver celery_app.py).
"""
from __future__ import annotations

import dataclasses
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from vigia_connectors import InfoLegClient, InfoLegNorm
from vigia_workers.celery_app import celery_app
from vigia_workers.persistence import run_async, upsert_normas, with_status

INFOLEG_SOURCE = {
    "code": "infoleg",
    "name": "InfoLEG — Base de legislación nacional (Min. Justicia)",
    "kind": "feed",
    "base_url": "https://datos.jus.gob.ar",
}

# Cuántos registros por batch al persistir el corpus completo.
_FULL_BATCH = 2000


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
def ingest_infoleg() -> dict[str, Any]:
    """Ingesta el muestreo de InfoLEG (~1000 normas). Rápido — bueno para dev."""

    async def _run() -> int:
        async with InfoLegClient() as client:
            normas = await client.fetch_sample()
        rows = [_norma_to_row(n) for n in normas]
        return await upsert_normas(INFOLEG_SOURCE, rows)

    async def _wrapped() -> dict[str, Any]:
        count = await with_status([INFOLEG_SOURCE["code"]], _run)
        return {"source": "infoleg", "mode": "sample", "rows": count}

    result = run_async(_wrapped())
    # Tras ingestar, cruzar contra las alertas activas y notificar.
    from vigia_workers.alerts import _match_all
    result["matching"] = run_async(_match_all())
    return result


@celery_app.task(name="vigia_workers.tasks.ingest_infoleg_full")
def ingest_infoleg_full() -> dict[str, Any]:
    """Ingesta el corpus completo de InfoLEG (~500k normas) por streaming.

    Descarga el ZIP a un temp file y persiste en batches para no cargar todo
    en memoria.
    """

    async def _run() -> int:
        total = 0
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "infoleg_full.zip"
            async with InfoLegClient() as client:
                await client.download_full_zip(dest)
            batch: list[dict[str, Any]] = []
            for norm in InfoLegClient.iter_full_zip(dest):
                batch.append(_norma_to_row(norm))
                if len(batch) >= _FULL_BATCH:
                    total += await upsert_normas(INFOLEG_SOURCE, batch)
                    batch = []
            if batch:
                total += await upsert_normas(INFOLEG_SOURCE, batch)
        return total

    async def _wrapped() -> dict[str, Any]:
        count = await with_status([INFOLEG_SOURCE["code"]], _run)
        return {"source": "infoleg", "mode": "full", "rows": count}

    return run_async(_wrapped())
