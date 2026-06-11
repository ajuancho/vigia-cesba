"""Jerarquía editorial del feed: qué es noticia y qué es trámite.

El BO publica ~100 items/día donde quizás 5 importan: sin esta separación el
feed muestra edictos de citación arriba de un DNU. Heurística simple y
auditable (sin IA — eso es Fase 5):

- DNU, LEY, COMUNICACION (BCRA) y CONSULTA: siempre destacados.
- PROYECTO: solo los de ley; declaraciones/resoluciones de cámara y
  beneplácitos/aniversarios son trámite (son el grueso del HCDN diario).
- Edictos/citaciones/remates (rubro "Aviso Oficial" del BORA) y los actos de
  personal (designaciones, renuncias, traslados, prórrogas): trámite.
"""
from __future__ import annotations

import re

# Actos de personal y administración interna (decretos/DA/resoluciones).
_TRAMITE_RE = re.compile(
    r"des[ií]gnase|designase|dase por designad|danse por designad"
    r"|ac[eé]ptase (la )?renuncia|aceptase (la )?renuncia|renuncia\.\s*$"
    r"|trasl[aá]dase|transfi[eé]rese|transfi[eé]rense|asignase funciones"
    r"|dase por finalizad|danse por prorrogad|prorr[oó]gase la designaci"
    r"|dase por aprobada la designaci|rech[aá]zase (el )?recurso|recurso de reconsideraci"
    r"|instr[uú]yase sumario|estructura organizativa - modificaci"
    r"|\bpromociones\.?\s*$|\bdesignaci[oó]n(es)?\.?\s*$|\bnombramientos?\.?\s*$",
    re.IGNORECASE,
)

# Proyectos parlamentarios ceremoniales (el grueso del ruido de HCDN).
_PROYECTO_CEREMONIAL_RE = re.compile(
    r"benepl[aá]cito|conmemoraci[oó]n|aniversario|expresar (pesar|repudio|preocupaci[oó]n|reconocimiento|adhesi[oó]n)"
    r"|declarar de inter[eé]s|d[ií]a (nacional|internacional|mundial) de",
    re.IGNORECASE,
)

# Orden editorial dentro de los destacados de una edición.
PESO_TIPO: dict[str, int] = {
    "DNU": 0, "LEY": 1, "DECRETO": 2, "COMUNICACION": 3, "CONSULTA": 4,
    "RESOLUCION": 5, "DISPOSICION": 6, "PROYECTO": 7, "OTRA": 8,
}


def es_tramite(
    tipo: str,
    titulo: str | None,
    *,
    tags: list[str] | None = None,
    tipo_linea: str | None = None,
) -> bool:
    """True si el item es trámite (va colapsado), False si es destacado."""
    if tipo in ("DNU", "LEY", "COMUNICACION", "CONSULTA"):
        return False
    t = titulo or ""
    if tipo == "PROYECTO":
        # tags trae el tipo de proyecto HCDN en minúsculas ("ley", "declaracion", ...)
        if tags and any(x in ("declaracion", "resolucion", "comunicacion") for x in tags):
            return True
        return bool(_PROYECTO_CEREMONIAL_RE.search(t))
    # Edictos, citaciones, remates: el listado del BORA los marca "Aviso Oficial".
    if (tipo_linea or "").strip().lower().startswith("aviso oficial"):
        return True
    return bool(_TRAMITE_RE.search(t))
