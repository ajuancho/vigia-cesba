"""Tests del conector Senado: parsing del listado y del detalle (offline, fixtures)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from vigia_connectors.senado import parse_detalle, parse_listado

FIXTURES = Path(__file__).parent / "fixtures"


def _listado():
    html = (FIXTURES / "senado_listado.html").read_text(encoding="utf-8")
    return parse_listado(html)


def test_parse_listado_filas():
    ps = _listado()
    assert len(ps) >= 5
    p = ps[0]
    assert p.external_id == "1040/26-S-PL"
    assert p.tipo_codigo == "PL"
    assert p.origen == "S"
    assert p.tipo_slug() == "PROYECTO"
    assert "PROYECTO DE LEY" in p.extracto.upper()
    assert p.url.endswith("/verExp/1040.26/S/PL")


def test_external_id_unicos_y_formato():
    ps = _listado()
    ids = [p.external_id for p in ps]
    assert len(ids) == len(set(ids))  # sin duplicados
    for eid in ids:
        assert "/" in eid and eid.count("-") == 2  # nnnn/aa-ORIGEN-TIPO


def test_parse_detalle_fecha_y_autores():
    html = (FIXTURES / "senado_detalle.html").read_text(encoding="utf-8")
    det = parse_detalle(html)
    assert det["fecha"] == date(2026, 6, 12)  # Mesa de Entradas
    assert det["autores"] and "Valenzuela" in det["autores"][0]


def test_parse_listado_vacio():
    assert parse_listado("<html><body>nada</body></html>") == []
