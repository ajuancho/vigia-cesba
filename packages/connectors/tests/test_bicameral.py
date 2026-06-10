"""Tests del conector de dictámenes de la Comisión Bicameral DNU."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from vigia_connectors.bicameral import iter_dictamenes_bicameral, parse_dnu_ref

FIXTURES = Path(__file__).parent / "fixtures"


def test_iter_filtra_bicameral():
    ds = list(iter_dictamenes_bicameral(FIXTURES / "hcdn_dictamenes.csv"))
    # La fila de ACCION SOCIAL se descarta; quedan las 3 de la bicameral.
    assert [d.expediente_hcdn for d in ds] == ["HCDN182484", "HCDN182483", "HCDN999999"]
    assert ds[0].fecha == date(2016, 2, 25)
    assert ds[2].observaciones is None  # NA -> None


def test_veredicto_mayoria_manda():
    ds = {d.expediente_hcdn: d for d in iter_dictamenes_bicameral(FIXTURES / "hcdn_dictamenes.csv")}
    # Mayoría aprueba validez aunque la minoría diga invalidez.
    assert ds["HCDN182484"].veredicto() == "validez"
    # Mayoría declara invalidez aunque la minoría aconseje aprobar.
    assert ds["HCDN182483"].veredicto() == "invalidez"
    assert ds["HCDN999999"].veredicto() is None


def test_parse_dnu_ref_formatos():
    # Título real de proyecto de comunicación (fecha textual).
    assert parse_dnu_ref(
        "COMUNICACION DEL DECRETO DE NECESIDAD Y URGENCIA 223 DEL 25 DE ENERO DE 2016, "
        "POR EL CUAL SE SUSTITUYE LA DENOMINACION DEL MINISTERIO"
    ) == (223, 2016)
    # Variantes con barra.
    assert parse_dnu_ref("INVALIDEZ DEL DECRETO 391/20") == (391, 2020)
    assert parse_dnu_ref("DNU 70/2023 - BASES PARA LA RECONSTRUCCION") == (70, 2023)
    assert parse_dnu_ref("EL DECRETO 897/07 SOBRE FONDO DE GARANTIA") == (897, 2007)
    # Sin referencia.
    assert parse_dnu_ref("PROYECTO DE LEY SOBRE PRESUPUESTO") is None
    assert parse_dnu_ref(None) is None
    assert parse_dnu_ref("EL DECRETO MENCIONADO") is None
