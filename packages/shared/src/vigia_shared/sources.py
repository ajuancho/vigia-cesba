"""Registry central de fuentes de datos.

Única definición del universo de fuentes esperadas. Lo consumen:
- los workers (tasks de ingesta + `check_sources` de frescura), y
- la API (`GET /health/sources` calcula el flag `stale` contra estos SLOs).

Cada entrada declara, además de los campos de `source_catalog`:
- `cadence_hours`: cada cuánto debería correr la ingesta (beat).
- `freshness_slo_days`: máxima antigüedad tolerada de la norma más reciente
  (`MAX(fecha_publicacion)`). Es la señal que detecta el caso "la task corre
  ok pero el dataset upstream dejó de avanzar".
"""
from __future__ import annotations

SOURCES: dict[str, dict] = {
    "infoleg": {
        "code": "infoleg",
        "name": "InfoLEG — Base de legislación nacional (Min. Justicia)",
        "kind": "feed",
        "base_url": "https://datos.jus.gob.ar",
        "cadence_hours": 24,
        # El dataset upstream se refresca ~mensualmente con lag: tolerar hasta 20 días.
        "freshness_slo_days": 20,
    },
    "hcdn_proyectos": {
        "code": "hcdn_proyectos",
        "name": "HCDN — Proyectos parlamentarios (datos.hcdn.gob.ar)",
        "kind": "feed",
        "base_url": "https://datos.hcdn.gob.ar",
        "cadence_hours": 24,
        "freshness_slo_days": 10,
    },
}

# Campos que van a la tabla source_catalog (los upserta cada task de ingesta).
_CATALOG_FIELDS = ("code", "name", "kind", "base_url")


def catalog_fields(code: str) -> dict:
    """Subset de SOURCES[code] con el shape que espera `upsert_normas`/`_upsert_source`."""
    src = SOURCES[code]
    return {k: src[k] for k in _CATALOG_FIELDS}
