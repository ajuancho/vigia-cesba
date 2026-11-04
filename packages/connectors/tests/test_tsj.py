"""Tests del conector del Tribunal Superior de Justicia: parsing de una página
real del buscador de jurisprudencia y paginación."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from vigia_connectors.tsj import Sentencia, TsjClient, parse_resultados

FIXTURES = Path(__file__).parent / "fixtures"


def _pagina():
    # Página 5 de 5 (resoluciones de octubre de 2026, 100 por página).
    return parse_resultados((FIXTURES / "tsj_resultados.html").read_bytes().decode("utf-8", "replace"))


def test_filas_y_total():
    filas, total = _pagina()
    assert total == 428
    assert len(filas) == 28


def test_campos_de_una_sentencia():
    s = _pagina()[0][0]
    assert s.expediente == "134000"
    assert s.secretaria == "SAL"
    assert s.secretaria_nombre == "Asuntos Laborales"
    assert s.fecha == date(2026, 10, 7)
    assert s.caratula.startswith("EXPERTA ART S.A.")
    assert s.tesauro[0] == "QUEJA POR DENEGACION DEL RECURSO DE INCONSTITUCIONALIDAD"
    assert s.url_pdf == (
        "https://www.tsjbaires.gov.ar/components/com_expedientes/expedientes_download_EJE.php"
        "?expediente=134000&anio=2025&incidente=0&movimiento=2399308"
    )


def test_utf8_pese_al_charset_declarado():
    caratulas = " ".join(s.caratula for s in _pagina()[0])
    assert "Ã" not in caratulas  # sin mojibake de leer UTF-8 como Latin-1


def test_ids_unicos_por_resolucion():
    filas = _pagina()[0]
    assert len({s.external_id for s in filas}) == len(filas)
    assert all(s.url_pdf for s in filas)


@pytest.mark.asyncio
async def test_pagina_hasta_completar_el_total():
    client = TsjClient()
    paginas = []

    async def fake(desde, hasta, pag):
        paginas.append(pag)
        filas = [Sentencia(expediente=str(pag * 1000 + i), caratula="x", secretaria="SAL",
                           fecha=desde, movimiento=str(pag * 1000 + i)) for i in range(100 if pag < 3 else 5)]
        return filas, 205

    client._pagina = AsyncMock(side_effect=fake)
    r = await client.fetch_rango(date(2026, 10, 1), date(2026, 10, 31))
    await client.aclose()
    assert paginas == [1, 2, 3]
    assert len(r) == 205
