"""Shape-tests de los mappers de ingesta.

Garantizan que cada `_to_row()` produce exactamente las columnas que
`upsert_normas` espera (las de `_NORMA_UPDATE_COLS` + external_id). Si un
conector nuevo agrega un mapper, su test de shape va acá: una key de más
rompe el INSERT; una de menos deja columnas viejas sin refrescar.
"""
from __future__ import annotations

from datetime import date

from vigia_connectors import HcdnProyecto, InfoLegNorm
from vigia_workers.persistence import _NORMA_UPDATE_COLS
from vigia_workers.tasks import _norma_to_row, _proyecto_to_row

EXPECTED_KEYS = set(_NORMA_UPDATE_COLS) | {"external_id"}


def test_norma_to_row_shape():
    n = InfoLegNorm(
        id_norma="1",
        tipo_norma="Decreto",
        numero_norma="404",
        clase_norma="DNU",
        organismo_origen="PEN",
        fecha_sancion=date(2026, 5, 28),
        numero_boletin="35900",
        fecha_boletin=date(2026, 5, 29),
        pagina_boletin="1",
        titulo_resumido="ESTRUCTURA",
        titulo_sumario=None,
        texto_resumido=None,
        texto_original_url=None,
    )
    row = _norma_to_row(n)
    assert set(row.keys()) == EXPECTED_KEYS
    assert row["tipo"] == "DNU"  # clase_norma manda
    assert row["fecha_publicacion"] == date(2026, 5, 29)  # boletín > sanción
    assert row["estado"] == "Publicada"
    assert row["raw"]["fecha_boletin"] == "2026-05-29"  # dates serializadas


def test_proyecto_to_row_shape():
    p = HcdnProyecto(
        proyecto_id="2561-D-2026",
        titulo="T",
        fecha_publicacion=date(2026, 6, 2),
        camara_origen="Diputados",
        exp_diputados="2561-D-2026",
        exp_senado=None,
        tipo_proyecto="LEY",
        autor="PEREZ, Juan",
    )
    row = _proyecto_to_row(p)
    assert set(row.keys()) == EXPECTED_KEYS
    assert row["tipo"] == "PROYECTO"
    assert row["numero"] == "2561-D-2026"
    assert row["estado"] == "En trámite"
    assert row["tags"] == ["ley"]
