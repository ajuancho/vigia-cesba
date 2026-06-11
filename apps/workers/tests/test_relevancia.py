"""Tests de la jerarquía editorial del feed (destacado vs trámite)."""
from __future__ import annotations

from vigia_shared.relevancia import es_tramite


def test_tipos_siempre_destacados():
    assert not es_tramite("DNU", "Cualquier cosa")
    assert not es_tramite("LEY", "PRESUPUESTO GENERAL")
    assert not es_tramite("COMUNICACION", "Ratio de Cobertura de Liquidez")
    assert not es_tramite("CONSULTA", "Actualización del reglamento de pesas")


def test_decretos_de_personal_son_tramite():
    assert es_tramite("DECRETO", "DECTO-2026-436-APN-PTE - Desígnase Subsecretario de Asuntos Estratégicos.")
    assert es_tramite("DECRETO", "DECTO-2026-437-APN-PTE - Acéptase renuncia.")
    assert es_tramite("DECRETO", "DA-2026-21-APN-JGM - Trasládase agente.")
    # Casos reales de la edición del 10/06 que se filtraban como destacados:
    assert es_tramite("DECRETO", "DA-2026-10-APN-JGM - Transfiérense agentes.")
    assert es_tramite("DECRETO", "DECTO-2026-430-APN-PTE - Recházase recurso.")
    assert es_tramite("DECRETO", "DECTO-2026-434-APN-PTE - Promociones.")
    # Un decreto de alcance general NO es trámite.
    assert not es_tramite("DECRETO", "BASES PARA LA RECONSTRUCCION DE LA ECONOMIA ARGENTINA")
    assert not es_tramite("DECRETO", "DECTO-2026-438-APN-PTE - Disposiciones.")


def test_edictos_bora_son_tramite():
    # El listado del BORA marca estos avisos con tipo_linea "Aviso Oficial".
    assert es_tramite(
        "OTRA",
        "El Tribunal Fiscal de la Nación, Sala G, comunica por dos días...",
        tipo_linea="Aviso Oficial",
    )
    # Una OTRA sin esa marca (p.ej. acordada) queda destacada.
    assert not es_tramite("OTRA", "ACORDADA 15/2026 - CORTE SUPREMA DE JUSTICIA")


def test_proyectos_ceremoniales_son_tramite():
    assert es_tramite(
        "PROYECTO",
        "EXPRESAR BENEPLACITO POR LA CONMEMORACION DEL 82 ANIVERSARIO DE LA CIUDAD",
        tags=["declaracion"],
    )
    # Aunque el tag diga ley, un beneplácito es ceremonial.
    assert es_tramite("PROYECTO", "EXPRESAR BENEPLACITO POR EL ANIVERSARIO", tags=["ley"])
    # Un proyecto de ley sustantivo es destacado.
    assert not es_tramite(
        "PROYECTO",
        "SISTEMA NACIONAL DE BOMBEROS VOLUNTARIOS. MODIFICACION DEL ARTICULO 11",
        tags=["ley"],
    )


def test_resoluciones_regulatorias_destacadas():
    assert not es_tramite("RESOLUCION", "REFINERIA DEL NORTE SOCIEDAD ANONIMA - CUADROS TARIFARIOS")
    assert es_tramite("RESOLUCION", "Desígnase Directora Nacional de Migraciones.")
