"""Scope de jurisdicción para queries sobre `norma`.

Cuando VIGIA_JURISDICCION_SCOPE está definido en el entorno, todas las queries
que tocan la tabla `norma` deben pasar por `norma_filters()` y `scope_where()`
para que el filtro se aplique automáticamente, sin que el frontend sepa nada.

Uso en routers ORM (SQLAlchemy):

    from vigia_api.core.scope import norma_filters
    filters = norma_filters()           # [] o [Norma.jurisdiccion == "CABA"]
    select(Norma).where(*filters, ...)  # se compone con los filtros del usuario

Uso en routers SQL crudo (text()):

    from vigia_api.core.scope import scope_where
    where_sql, params = scope_where(existing_conditions, existing_params)
    # where_sql: "WHERE jurisdiccion = :_scope_jur AND ..."
    # params incluye la clave _scope_jur si aplica
"""
from __future__ import annotations

from vigia_api.core.settings import get_settings


def jurisdiccion_scope() -> str | None:
    """Devuelve la jurisdicción fija o None si no hay scope configurado."""
    v = get_settings().vigia_jurisdiccion_scope.strip()
    return v if v else None


def norma_filters() -> list:
    """Filtros SQLAlchemy listos para .where(*norma_filters(), ...).

    Devuelve lista vacía si no hay scope → sin overhead.
    """
    from vigia_shared.models import Norma

    jur = jurisdiccion_scope()
    if jur is None:
        return []
    return [Norma.jurisdiccion == jur]


def scope_where(
    conditions: list[str],
    params: dict,
) -> tuple[list[str], dict]:
    """Agrega la condición de scope a una lista de cláusulas WHERE (SQL crudo).

    Devuelve (conditions, params) con la condición inyectada si corresponde.
    No muta los argumentos originales.
    """
    jur = jurisdiccion_scope()
    if jur is None:
        return conditions, params
    return (
        [*conditions, "jurisdiccion = :_scope_jur"],
        {**params, "_scope_jur": jur},
    )
