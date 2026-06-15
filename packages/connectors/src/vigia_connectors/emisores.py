"""Etiquetado del emisor/organismo canónico por keywords (compartido por los conectores).

A diferencia de `sector` (temático: Energía, Salud…), el `emisor` identifica QUIÉN
dicta la norma y normaliza el `organismo` (texto libre, con variantes de tildes y
reorganizaciones como AFIP→ARCA) a una clave estable y faceteable. Se detecta sobre
el `organismo` (señal autoritativa); el resultado es la clave que el usuario filtra.
"""
from __future__ import annotations

import re
import unicodedata


def _norm(s: str) -> str:
    """Mayúsculas y sin tildes — matchea robusto contra variantes (COMISIÓN/COMISION)."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper()


# (clave canónica, frases largas [substring], siglas [límite de palabra]).
# El primer match gana: poné lo más específico arriba. Las frases ya van sin tildes.
_RULES: list[tuple[str, list[str], list[str]]] = [
    ("ARCA", [
        "ADMINISTRACION FEDERAL DE INGRESOS PUBLICOS",
        "AGENCIA DE RECAUDACION Y CONTROL ADUANERO",
        "DIRECCION GENERAL IMPOSITIVA",
        "DIRECCION GENERAL DE ADUANAS",
    ], ["AFIP", "ARCA", "DGI", "DGA"]),
    ("CNV", ["COMISION NACIONAL DE VALORES"], ["CNV"]),
    ("CNDC", ["DE LA COMPETENCIA"], ["CNDC"]),  # CNDC + Secretaría de (Defensa de la) Competencia
    ("BCRA", ["BANCO CENTRAL DE LA REPUBLICA ARGENTINA"], ["BCRA"]),
    ("ENACOM", ["ENTE NACIONAL DE COMUNICACIONES"], ["ENACOM"]),
    ("SSN", ["SUPERINTENDENCIA DE SEGUROS"], []),
    ("ENRE", ["ENTE NACIONAL REGULADOR DE LA ELECTRICIDAD"], ["ENRE"]),
    ("ENARGAS", ["ENTE NACIONAL REGULADOR DEL GAS"], ["ENARGAS"]),
    ("ANMAT", ["MEDICAMENTOS, ALIMENTOS Y TEC", "ADMINISTRACION NACIONAL DE MEDICAMENTOS"], ["ANMAT"]),
    ("UIF", ["UNIDAD DE INFORMACION FINANCIERA"], ["UIF"]),
    ("IGJ", ["INSPECCION GENERAL DE JUSTICIA"], ["IGJ"]),
    ("SENASA", ["SANIDAD Y CALIDAD AGROALIMENTARIA"], ["SENASA"]),
]


def detect_emisor(*parts: str | None) -> str | None:
    """Devuelve la clave del emisor cuyo patrón aparezca en el texto (o None).

    Pasá el `organismo` como señal principal: el emisor es quien dicta la norma.
    """
    haystack = _norm(" ".join(p for p in parts if p))
    if not haystack:
        return None
    for clave, frases, siglas in _RULES:
        if any(f in haystack for f in frases):
            return clave
        if siglas and re.search(r"\b(" + "|".join(siglas) + r")\b", haystack):
            return clave
    return None


# Catálogo de emisores conocidos (para validación/UI). Orden por relevancia.
EMISORES: list[str] = [clave for clave, _, _ in _RULES]
