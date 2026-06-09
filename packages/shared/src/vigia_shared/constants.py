"""Constantes de dominio de Vigía.

Portadas del frontend mock original (`src/data/mockData.js`) para que backend
y frontend compartan el mismo vocabulario de tipos/sectores/jurisdicciones.
"""
from __future__ import annotations

# Tipo de norma -> metadata para UI. El `slug` es lo que se guarda en `norma.tipo`.
TIPOS_NORMA: dict[str, dict[str, str]] = {
    "DNU": {"label": "DNU", "description": "Decreto de Necesidad y Urgencia"},
    "DECRETO": {"label": "Decreto", "description": "Decreto del Poder Ejecutivo"},
    "LEY": {"label": "Ley", "description": "Ley sancionada por el Congreso"},
    "RESOLUCION": {"label": "Resolución", "description": "Resolución ministerial"},
    "DISPOSICION": {"label": "Disposición", "description": "Disposición administrativa"},
    "PROYECTO": {"label": "Proyecto", "description": "Proyecto de ley en trámite"},
    "OTRA": {"label": "Otra", "description": "Otra norma"},
}

JURISDICCIONES: list[str] = [
    "Nacional", "Buenos Aires", "CABA", "Córdoba", "Santa Fe",
    "Mendoza", "Tucumán", "Entre Ríos",
]

SECTORES: list[str] = [
    "Economía", "Energía", "Salud", "Educación", "Justicia", "Trabajo",
    "Ambiente", "Tecnología", "Comercio", "Transporte", "Minería", "Agro",
    "Defensa", "Seguridad",
]

IMPACTOS: list[str] = ["alto", "medio", "bajo"]
