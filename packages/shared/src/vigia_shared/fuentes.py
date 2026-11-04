"""Fuentes de la instancia CESBA y cómo distinguirlas en la tabla `norma`.

- ``boletin``: normas del Boletín Oficial CABA (cualquier `bora_seccion` que
  no sea de otra fuente, o sin sección).
- ``legislatura``: expedientes de la Legislatura porteña
  (`bora_seccion = 'Legislatura'`, worker `ingest_legislatura`).
- ``tsj``: sentencias del Tribunal Superior de Justicia
  (`bora_seccion = 'Tribunal Superior'`, worker `ingest_tsj`).

Lo usan el buscador, las alertas y el feed para filtrar por fuente.
"""
from __future__ import annotations

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


def fuentes_sql(fuentes: list[str], alias: str = "") -> str | None:
    """OR de varias fuentes; None si la lista está vacía (= todas)."""
    validas = [f for f in fuentes if f in FUENTES]
    if not validas or set(validas) == set(FUENTES):
        return None
    return "(" + " OR ".join(fuente_sql(f, alias) for f in validas) + ")"
