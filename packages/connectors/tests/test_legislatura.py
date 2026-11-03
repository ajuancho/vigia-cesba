"""Tests del conector de la Legislatura porteña: parsing del XML real del web
service y partición de ventanas cuando una consulta viene llena."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from vigia_connectors.legislatura import LegislaturaClient, parse_expedientes

FIXTURES = Path(__file__).parent / "fixtures"


def _expedientes():
    return parse_expedientes((FIXTURES / "legislatura_expedientes.xml").read_bytes())


def test_parsea_todos_los_expedientes():
    # Respuesta real de GetExpedienteAvanzada, 27/10/2026 al 02/11/2026.
    assert len(_expedientes()) == 78


def test_campos_del_primer_expediente():
    e = _expedientes()[0]
    assert e.id_expediente == 143054
    assert e.numero == "3425-D-2026"
    assert e.fecha_inicio == datetime(2026, 10, 30, 16, 35, 3)
    assert e.fecha_movimiento == datetime(2026, 11, 3, 14, 40, 56)  # día sin cero a la izquierda
    assert e.tipo == "LEY"
    assert e.tipo_nombre == "Proyecto de ley"
    assert e.autor == "GONZÁLEZ, ANDREA MARIANA"
    assert len(e.coautores) == 12
    assert e.origen == "Diputados/as"
    assert e.sancionado is False
    assert e.estado.startswith("ESPERANDO ENVIO A COMISION")
    assert e.url == "https://parlamentaria.legislatura.gob.ar/pages/expediente.aspx?id=143054"
    assert e.url_documento == "https://parlamentaria.legislatura.gob.ar/pages/download.aspx?IdDoc=228310"


def test_tipos_legibles():
    tipos = {e.tipo: e.tipo_nombre for e in _expedientes()}
    assert tipos["RESOLUCION"] == "Proyecto de resolución"
    assert tipos["DECLARACION"] == "Proyecto de declaración"
    assert tipos["ESCUELAS"] == "Escuelas"


def test_sin_coautores_ni_documento():
    sin_coautores = [e for e in _expedientes() if not e.coautores]
    assert sin_coautores, "el fixture tiene expedientes sin coautores"
    assert all(isinstance(e.coautores, list) for e in sin_coautores)


@pytest.mark.asyncio
async def test_parte_la_ventana_si_viene_llena():
    client = LegislaturaClient()
    lleno = [object()] * 950
    llamadas = []

    async def fake(desde, hasta):
        llamadas.append((desde, hasta))
        return lleno if (hasta - desde).days >= 6 else []

    client._avanzada = AsyncMock(side_effect=fake)
    await client.fetch_rango(date(2026, 10, 1), date(2026, 10, 7))
    await client.aclose()
    # La ventana de 7 días vino "llena" → se partió en dos mitades.
    assert llamadas[0] == (date(2026, 10, 1), date(2026, 10, 7))
    assert (date(2026, 10, 1), date(2026, 10, 4)) in llamadas
    assert (date(2026, 10, 5), date(2026, 10, 7)) in llamadas
