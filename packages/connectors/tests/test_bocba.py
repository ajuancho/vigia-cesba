"""Tests del conector BOCBA: parsing de la respuesta JSON, clasificación y sectores."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from vigia_connectors.bocba import (
    BocbaNorma,
    BocbaClient,
    _iter_normas,
    _parse_fecha,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture() -> dict:
    return json.loads((FIXTURES / "bocba_boletin.json").read_text(encoding="utf-8"))


def _normas() -> list[BocbaNorma]:
    data = _load_fixture()
    numero = data["boletin"]["numero"]
    fecha = _parse_fecha(data["boletin"]["fecha_publicacion"])
    normas_raw = data["normas"]["normas"]
    return _iter_normas(normas_raw, numero, fecha)


# ---------------------------------------------------------------------------
# Parsing básico
# ---------------------------------------------------------------------------

def test_total_normas():
    normas = _normas()
    # El boletín del 18-06-2026 tiene 429 normas en la sección principal.
    assert len(normas) == 429


def test_metadata_boletin():
    data = _load_fixture()
    assert data["boletin"]["numero"] == 7390
    assert data["boletin"]["fecha_publicacion"] == "18/06/2026"


def test_parse_fecha():
    assert _parse_fecha("18/06/2026") == date(2026, 6, 18)
    assert _parse_fecha("2026-06-18") == date(2026, 6, 18)
    assert _parse_fecha("garbage") is None


def test_campos_basicos():
    normas = {n.id_norma: n for n in _normas()}
    # Resolución del Poder Legislativo capturada en la fixture.
    n = normas[981570]
    assert n.nombre == "Resolución N° 321/SA/26"
    assert n.organismo == "Legislatura de la Ciudad de Buenos Aires"
    assert n.seccion == "legislativo"
    assert n.seccion_nombre == "Poder Legislativo"
    assert n.tipo_nombre == "Resolución"
    assert n.fecha == date(2026, 6, 18)
    assert n.numero_boletin == 7390
    assert n.sumario is not None
    assert "ciberseguridad" in n.sumario.lower()


# ---------------------------------------------------------------------------
# Extracción de número
# ---------------------------------------------------------------------------

def test_numero_resolucion():
    normas = {n.id_norma: n for n in _normas()}
    n = normas[981570]
    assert n.numero == "321/SA/26"


def test_numero_decreto():
    normas = _normas()
    decretos = [n for n in normas if n.tipo_nombre == "Decreto"]
    assert decretos, "debe haber al menos un decreto en la fixture"
    d = decretos[0]
    assert d.numero is not None
    assert "/" not in d.numero or d.numero.replace("/", "").isdigit() or len(d.numero) < 20


# ---------------------------------------------------------------------------
# Clasificación tipo_slug
# ---------------------------------------------------------------------------

def test_tipo_slug_resolucion():
    n = BocbaNorma(
        id_norma=1, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="ejecutivo", seccion_nombre="Poder Ejecutivo",
        tipo_nombre="Resolución", organismo="Min. Salud",
        nombre="Resolución N° 100/MSGC/26", sumario=None,
        url_norma="http://example.com",
    )
    assert n.tipo_slug() == "RESOLUCION"


def test_tipo_slug_decreto():
    n = BocbaNorma(
        id_norma=2, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="ejecutivo", seccion_nombre="Poder Ejecutivo",
        tipo_nombre="Decreto", organismo="Área Jefe de Gobierno",
        nombre="Decreto N° 223", sumario=None,
        url_norma="http://example.com",
    )
    assert n.tipo_slug() == "DECRETO"


def test_tipo_slug_disposicion():
    n = BocbaNorma(
        id_norma=3, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="ejecutivo", seccion_nombre="Poder Ejecutivo",
        tipo_nombre="Disposición", organismo="DGCYC",
        nombre="Disposición N° 30/DGCYC/26", sumario=None,
        url_norma="http://example.com",
    )
    assert n.tipo_slug() == "DISPOSICION"


def test_tipo_slug_ley():
    n = BocbaNorma(
        id_norma=4, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="legislativo", seccion_nombre="Poder Legislativo",
        tipo_nombre="Ley", organismo="Legislatura CABA",
        nombre="Ley N° 7100", sumario=None,
        url_norma="http://example.com",
    )
    assert n.tipo_slug() == "LEY"


def test_tipo_slug_desconocido():
    n = BocbaNorma(
        id_norma=5, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="avisos", seccion_nombre="Comunicados y Avisos",
        tipo_nombre="Edicto Notarial", organismo="Notaría",
        nombre="Edicto 12/26", sumario=None,
        url_norma="http://example.com",
    )
    assert n.tipo_slug() == "OTRA"


# ---------------------------------------------------------------------------
# Distribución por sección (smoke test sobre fixture real)
# ---------------------------------------------------------------------------

def test_distribucion_secciones():
    from collections import Counter
    normas = _normas()
    conteo = Counter(n.seccion for n in normas)
    # La fixture tiene la distribución del 18-06-2026.
    assert conteo["ejecutivo"] > 100
    assert conteo["avisos"] > 0
    assert conteo["licitaciones"] > 0
    assert conteo["legislativo"] > 0


# ---------------------------------------------------------------------------
# Detección de sector
# ---------------------------------------------------------------------------

def test_sector_tecnologia():
    n = BocbaNorma(
        id_norma=10, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="legislativo", seccion_nombre="Poder Legislativo",
        tipo_nombre="Resolución", organismo="Legislatura de la Ciudad de Buenos Aires",
        nombre="Resolución N° 321/SA/26",
        sumario="Aprueba pliegos para la contratación de plataforma de ciberseguridad.",
        url_norma="http://example.com",
    )
    assert n.detect_sector() == "Tecnología"


def test_sector_salud():
    n = BocbaNorma(
        id_norma=11, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="ejecutivo", seccion_nombre="Poder Ejecutivo",
        tipo_nombre="Decreto", organismo="Área Jefe de Gobierno",
        nombre="Decreto N° 223",
        sumario="Convalida listado de docentes para Hospital de Rehabilitación.",
        url_norma="http://example.com",
    )
    assert n.detect_sector() == "Salud"


def test_sector_none_cuando_no_hay_keywords():
    n = BocbaNorma(
        id_norma=12, numero_boletin=7390, fecha=date(2026, 6, 18),
        seccion="ejecutivo", seccion_nombre="Poder Ejecutivo",
        tipo_nombre="Resolución", organismo="Secretaría General",
        nombre="Resolución N° 5/SG/26",
        sumario="Establece el cronograma de reuniones internas del área.",
        url_norma="http://example.com",
    )
    assert n.detect_sector() is None


# ---------------------------------------------------------------------------
# Día sin boletín (API devuelve errores)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dia_sin_boletin_devuelve_lista_vacia():
    """Un sábado no tiene boletín — la API devuelve {errores: [...]}."""
    error_response = {"errores": ["No existe boletín para esa fecha."]}
    with patch(
        "vigia_connectors.bocba.get_json",
        new_callable=AsyncMock,
        return_value=error_response,
    ):
        async with BocbaClient() as client:
            normas = await client.fetch_boletin(date(2026, 6, 14))  # sábado
    assert normas == []


# ---------------------------------------------------------------------------
# Cliente: estructura del request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_client_llama_endpoint_correcto():
    """El cliente construye la URL con formato dd-mm-yyyy y carga_datos=true."""
    data = _load_fixture()
    with patch(
        "vigia_connectors.bocba.get_json",
        new_callable=AsyncMock,
        return_value=data,
    ) as mock_get:
        async with BocbaClient() as client:
            normas = await client.fetch_boletin(date(2026, 6, 18))

    mock_get.assert_called_once()
    path_arg = mock_get.call_args[0][1]  # segundo arg posicional = path
    assert path_arg == "/obtenerBoletin/18-06-2026/true"
    assert len(normas) == 429


@pytest.mark.asyncio
async def test_client_acepta_numero_de_boletin():
    """Se puede pedir un boletín por número en lugar de fecha."""
    data = _load_fixture()
    with patch(
        "vigia_connectors.bocba.get_json",
        new_callable=AsyncMock,
        return_value=data,
    ) as mock_get:
        async with BocbaClient() as client:
            await client.fetch_boletin(numero=7390)

    path_arg = mock_get.call_args[0][1]
    assert path_arg == "/obtenerBoletin/7390/true"
