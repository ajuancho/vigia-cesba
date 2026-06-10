"""Tests del etiquetado de sector por keywords."""
from __future__ import annotations

from vigia_connectors.sectores import detect_sector


def test_match_simple():
    assert detect_sector("Régimen de promoción de VACA MUERTA") == "Energía"
    assert detect_sector("ANMAT — registro de medicamentos") == "Salud"
    assert detect_sector("Resolución del BANCO CENTRAL") == "Economía"


def test_combina_partes_y_none():
    assert detect_sector(None, "exploración de LITIO", None) == "Minería"


def test_primer_match_gana():
    # "ENERGÍA" (regla 1) aparece antes que "TRIBUTARI" (regla Economía).
    assert detect_sector("ENERGÍA: nuevo régimen tributario") == "Energía"


def test_sin_match():
    assert detect_sector("Declaración de interés municipal") is None
    assert detect_sector() is None
    assert detect_sector(None, "") is None
