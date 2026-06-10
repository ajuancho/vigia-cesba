"""Tests del conector InfoLEG: clasificación de tipo y parsing de filas."""
from __future__ import annotations

from datetime import date

from vigia_connectors.infoleg import InfoLegClient, InfoLegNorm, _parse_date


def _norm(**overrides) -> InfoLegNorm:
    base = dict(
        id_norma="123",
        tipo_norma="Decreto",
        numero_norma="70/2023",
        clase_norma=None,
        organismo_origen="PODER EJECUTIVO NACIONAL (P.E.N.)",
        fecha_sancion=date(2023, 12, 20),
        numero_boletin="35321",
        fecha_boletin=date(2023, 12, 21),
        pagina_boletin="3",
        titulo_resumido="BASES PARA LA RECONSTRUCCION",
        titulo_sumario=None,
        texto_resumido=None,
        texto_original_url=None,
    )
    base.update(overrides)
    return InfoLegNorm(**base)


class TestTipoSlug:
    def test_dnu_via_clase_norma(self):
        # Gotcha InfoLEG: los DNU vienen como tipo="Decreto" + clase="DNU".
        # La clase se evalúa PRIMERO.
        assert _norm(tipo_norma="Decreto", clase_norma="DNU").tipo_slug() == "DNU"

    def test_dnu_via_clase_descriptiva(self):
        assert _norm(clase_norma="Decreto de Necesidad y Urgencia").tipo_slug() == "DNU"

    def test_decreto_comun(self):
        assert _norm(tipo_norma="Decreto", clase_norma=None).tipo_slug() == "DECRETO"

    def test_ley(self):
        assert _norm(tipo_norma="Ley").tipo_slug() == "LEY"

    def test_resolucion(self):
        assert _norm(tipo_norma="Resolución").tipo_slug() == "RESOLUCION"

    def test_disposicion(self):
        assert _norm(tipo_norma="Disposición").tipo_slug() == "DISPOSICION"

    def test_decision_administrativa_es_decreto(self):
        assert _norm(tipo_norma="Decisión Administrativa").tipo_slug() == "DECRETO"

    def test_desconocido_es_otra(self):
        assert _norm(tipo_norma="Acordada").tipo_slug() == "OTRA"


class TestRowToNorm:
    def test_fila_completa(self):
        n = InfoLegClient._row_to_norm(
            {
                "id_norma": " 99 ",
                "tipo_norma": "Ley",
                "numero_norma": "27000",
                "clase_norma": "",
                "organismo_origen": "HONORABLE CONGRESO DE LA NACION ARGENTINA",
                "fecha_sancion": "2014-10-01",
                "numero_boletin": "33000",
                "fecha_boletin": "29/10/2014",
                "pagina_boletin": "1",
                "titulo_resumido": "PRESUPUESTO",
                "titulo_sumario": "",
                "texto_resumido": "",
                "texto_original": "http://servicios.infoleg.gob.ar/x.htm",
            }
        )
        assert n is not None
        assert n.id_norma == "99"
        assert n.fecha_sancion == date(2014, 10, 1)
        assert n.fecha_boletin == date(2014, 10, 29)  # formato dd/mm/yyyy
        assert n.clase_norma is None  # string vacío -> None
        assert n.texto_original_url == "http://servicios.infoleg.gob.ar/x.htm"

    def test_sin_id_descarta(self):
        assert InfoLegClient._row_to_norm({"id_norma": "", "tipo_norma": "Ley"}) is None


def test_parse_date_formatos():
    assert _parse_date("2026-06-10") == date(2026, 6, 10)
    assert _parse_date("10/06/2026") == date(2026, 6, 10)
    assert _parse_date("2026/06/10") == date(2026, 6, 10)
    assert _parse_date("") is None
    assert _parse_date("no-fecha") is None
