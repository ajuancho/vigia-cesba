"""Tests del conector HCDN: parsing de filas CSV y derivados."""
from __future__ import annotations

from datetime import date

from vigia_connectors.hcdn import HcdnClient, _na, _parse_fecha


def test_row_to_proyecto_completo():
    p = HcdnClient._row_to_proyecto(
        {
            "PROYECTO_ID": " 2561-D-2026 ",
            "TITULO": "EXPRESAR BENEPLACITO ...",
            "PUBLICACION_FECHA": "2026-06-02",
            "CAMARA_ORIGEN": "Diputados",
            "EXP_DIPUTADOS": "2561-D-2026",
            "EXP_SENADO": "NA",
            "TIPO": "DECLARACION",
            "AUTOR": "PEREZ, Juan",
        }
    )
    assert p is not None
    assert p.proyecto_id == "2561-D-2026"
    assert p.fecha_publicacion == date(2026, 6, 2)
    assert p.exp_senado is None  # "NA" -> None
    assert p.expediente == "2561-D-2026"  # diputados gana si existe
    assert p.organismo() == "Honorable Cámara de Diputados de la Nación"
    assert p.tipo_proyecto == "DECLARACION"


def test_origen_senado():
    p = HcdnClient._row_to_proyecto(
        {
            "PROYECTO_ID": "S-100/26",
            "TITULO": "T",
            "CAMARA_ORIGEN": "Senado De La Nación",
            "EXP_DIPUTADOS": "NA",
            "EXP_SENADO": "S-100/26",
        }
    )
    assert p is not None
    assert p.organismo() == "Honorable Senado de la Nación"
    assert p.expediente == "S-100/26"  # fallback a senado


def test_filas_invalidas_se_descartan():
    assert HcdnClient._row_to_proyecto({"PROYECTO_ID": "", "TITULO": "x"}) is None
    assert HcdnClient._row_to_proyecto({"PROYECTO_ID": "1", "TITULO": ""}) is None


def test_parse_fecha():
    assert _parse_fecha("2026-06-02") == date(2026, 6, 2)
    assert _parse_fecha("2026-06-02T00:00:00Z") == date(2026, 6, 2)
    assert _parse_fecha("NA") is None
    assert _parse_fecha(None) is None


def test_na():
    assert _na("NA") is None
    assert _na("na") is None
    assert _na("  ") is None
    assert _na("valor") == "valor"
