"""Fuentes de la instancia CESBA y cómo distinguirlas en la tabla `norma`.

- ``boletin``: normas del Boletín Oficial CABA (cualquier `bora_seccion` salvo
  la de la Legislatura, o sin sección).
- ``legislatura``: expedientes de la Legislatura porteña
  (`bora_seccion = 'Legislatura'`, worker `ingest_legislatura`).

Lo usan el buscador, las alertas y el feed para filtrar por fuente.
"""
from __future__ import annotations

SECCION_LEGISLATURA = "Legislatura"

FUENTES = {
    "boletin": "Boletín Oficial",
    "legislatura": "Legislatura",
}


def fuente_sql(fuente: str, alias: str = "") -> str:
    """Condición SQL (sin parámetros) para una fuente. `alias` = prefijo de tabla."""
    col = f"{alias}.bora_seccion" if alias else "bora_seccion"
    if fuente == "legislatura":
        return f"{col} = '{SECCION_LEGISLATURA}'"
    if fuente == "boletin":
        return f"({col} IS NULL OR {col} <> '{SECCION_LEGISLATURA}')"
    raise ValueError(f"fuente desconocida: {fuente}")


def fuentes_sql(fuentes: list[str], alias: str = "") -> str | None:
    """OR de varias fuentes; None si la lista está vacía (= todas)."""
    validas = [f for f in fuentes if f in FUENTES]
    if not validas or set(validas) == set(FUENTES):
        return None
    return "(" + " OR ".join(fuente_sql(f, alias) for f in validas) + ")"
