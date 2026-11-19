"""Fuentes de la instancia nuevosBAires y cómo distinguirlas en la tabla `norma`.

- ``boletin``: normas del Boletín Oficial CABA (cualquier `bora_seccion` que
  no sea de otra fuente, o sin sección).
- ``legislatura``: expedientes de la Legislatura porteña
  (`bora_seccion = 'Legislatura'`, worker `ingest_legislatura`).
- ``tsj``: sentencias del Tribunal Superior de Justicia
  (`bora_seccion = 'Tribunal Superior'`, worker `ingest_tsj`).

Lo usan el buscador, las alertas y el feed para filtrar por fuente.
"""
from __future__ import annotations

import re
import unicodedata

SECCION_LEGISLATURA = "Legislatura"
SECCION_TSJ = "Tribunal Superior"

FUENTES = {
    "boletin": "Boletín Oficial",
    "legislatura": "Legislatura",
    "tsj": "Tribunal Superior",
}

# Secciones que NO son del Boletín (cada una es una fuente propia).
SECCIONES_EXTERNAS = {"legislatura": SECCION_LEGISLATURA, "tsj": SECCION_TSJ}


def fuente_sql(fuente: str, alias: str = "") -> str:
    """Condición SQL (sin parámetros) para una fuente. `alias` = prefijo de tabla."""
    col = f"{alias}.bora_seccion" if alias else "bora_seccion"
    if fuente in SECCIONES_EXTERNAS:
        return f"{col} = '{SECCIONES_EXTERNAS[fuente]}'"
    if fuente == "boletin":
        externas = ", ".join(f"'{s}'" for s in SECCIONES_EXTERNAS.values())
        return f"({col} IS NULL OR {col} NOT IN ({externas}))"
    raise ValueError(f"fuente desconocida: {fuente}")


# Frases que nombran una fuente (sin tildes, en minúscula; las más largas primero).
_FRASES_FUENTE: list[tuple[str, str]] = [
    ("boletin oficial de la ciudad de buenos aires", "boletin"),
    ("boletin oficial de la ciudad", "boletin"),
    ("boletin oficial", "boletin"),
    ("bocba", "boletin"),
    ("boletin", "boletin"),
    ("legislatura portena", "legislatura"),
    ("legislatura de la ciudad", "legislatura"),
    ("legislatura", "legislatura"),
    ("tribunal superior de justicia", "tsj"),
    ("tribunal superior", "tsj"),
    ("tsj", "tsj"),
    ("sentencias", "tsj"),
]
_CONECTORES = "en|del|de|la|el|los|las|por|y|o"


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def quitar_fuentes(texto: str) -> tuple[list[str], str]:
    """Detecta nombres de fuente en un texto de búsqueda y los quita.

    "vivienda boletín oficial" → (["boletin"], "vivienda"). Las fuentes no
    aparecen en el texto de las normas, así que buscarlas como palabras no
    devuelve nada: se aplican como filtro. Se llevan también los conectores
    que las preceden ("vivienda en el Boletín Oficial" → "vivienda").
    """
    plano = _sin_tildes(texto).lower()
    if len(plano) != len(texto):  # caracteres combinados: se trabaja sobre la versión plana
        texto = plano
    encontradas: list[str] = []
    cortes: list[tuple[int, int]] = []
    for frase, fuente in _FRASES_FUENTE:
        patron = rf"(?:(?<!\w)(?:{_CONECTORES})\s+)*(?<![\w-]){re.escape(frase)}(?!\w)"
        for m in re.finditer(patron, plano):
            if any(a < m.end() and m.start() < b for a, b in cortes):
                continue
            cortes.append((m.start(), m.end()))
            if fuente not in encontradas:
                encontradas.append(fuente)
    if not cortes:
        return [], texto.strip()
    partes, prev = [], 0
    for a, b in sorted(cortes):
        partes.append(texto[prev:a])
        prev = b
    partes.append(texto[prev:])
    return encontradas, re.sub(r"\s+", " ", " ".join(partes)).strip()


def fuentes_sql(fuentes: list[str], alias: str = "") -> str | None:
    """OR de varias fuentes; None si la lista está vacía (= todas)."""
    validas = [f for f in fuentes if f in FUENTES]
    if not validas or set(validas) == set(FUENTES):
        return None
    return "(" + " OR ".join(fuente_sql(f, alias) for f in validas) + ")"
