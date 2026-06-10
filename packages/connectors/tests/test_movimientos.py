"""Tests de movimientos HCDN: parsing del CSV y derivación de estado."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from vigia_connectors.hcdn import HcdnClient, clasificar_movimiento, derivar_estado

FIXTURES = Path(__file__).parent / "fixtures"


def test_iter_movimientos_descarta_na():
    movs = list(HcdnClient.iter_movimientos_csv(FIXTURES / "hcdn_movimientos.csv"))
    # La fila toda-NA se descarta; quedan 7 con texto.
    assert len(movs) == 7
    assert movs[1].proyecto_id == "HCDN100002"
    assert movs[1].fecha == date(2026, 3, 10)
    assert movs[2].fecha is None  # NA


def test_clasificar_movimiento():
    assert clasificar_movimiento("PASA A SENADO - ") == (5, "Media sanción")
    assert clasificar_movimiento("DICTAMEN DE COMISION") == (3, "Con dictamen")
    assert clasificar_movimiento("GIRO A LA COMISION DE ENERGIA") == (1, "En comisión")
    assert clasificar_movimiento("SOLICITUD DE SER COFIRMANTE") is None
    assert clasificar_movimiento(None) is None


def test_derivar_estado_toma_el_mayor_rango():
    # El proyecto pasó por giro → dictamen → aprobación → media sanción:
    # gana "Media sanción" aunque las fechas vengan NA (sin orden confiable).
    assert derivar_estado([
        "GIRO A LA COMISION DE PRESUPUESTO",
        "DICTAMEN DE COMISION CON DISIDENCIAS",
        "CONSIDERACION Y APROBACION",
        "PASA A SENADO - ",
    ]) == "Media sanción"
    # Resolución/declaración aprobada por art. 114: terminal "Aprobado".
    assert derivar_estado(["APROBACION ARTICULO 114 DEL REGLAMENTO"]) == "Aprobado"
    assert derivar_estado(["PASA AL ARCHIVO (LEY 13640)"]) == "Archivado"
    # Solo movimientos administrativos: sin estado derivado.
    assert derivar_estado(["SOLICITUD DE SER COFIRMANTE"]) is None
    assert derivar_estado([]) is None
