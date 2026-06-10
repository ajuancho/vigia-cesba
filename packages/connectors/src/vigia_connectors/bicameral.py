"""Comisión Bicameral Permanente de Trámite Legislativo (ley 26.122) — dictámenes de DNU.

Fuente estructurada: dataset CKAN `dictamenes` de datos.hcdn.gob.ar. Las filas
con GIRO = "BICAMERAL PERMANENTE DE TRAMITE LEGISLATIVO - LEY 26122" son los
dictámenes de la comisión (~520 desde 2008, se actualiza eventual).

El join al DNU es indirecto pero limpio (verificado 2026-06):
- `EXPEDIENTE` del dictamen (p.ej. "HCDN182484") == `PROYECTO_ID` del dataset
  `proyectos-parlamentarios` == `norma.external_id` de la fuente
  `hcdn_proyectos` que Vigía ya ingiere a diario.
- El TITULO de ese proyecto referencia el DNU: "COMUNICACION DEL DECRETO DE
  NECESIDAD Y URGENCIA 223 DEL 25 DE ENERO DE 2016, ...".

El veredicto se deriva de OBSERVACIONES: el dictamen de MAYORÍA aconseja
declarar la VALIDEZ o INVALIDEZ del decreto. Ojo: un dictamen NO aprueba ni
rechaza el DNU (eso requiere resolución de ambas cámaras, art. 24 ley 26.122);
por eso el estado destino es "dictaminado", con el sentido en las notas.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from pathlib import Path
from typing import Iterator

DICTAMENES_PACKAGE_ID = "dictamenes"
_GIRO_BICAMERAL = "BICAMERAL PERMANENTE DE TRAMITE LEGISLATIVO"

# Referencia a un DNU en el título del proyecto de comunicación:
# "DECRETO DE NECESIDAD Y URGENCIA 223 DEL 25 DE ENERO DE 2016"
# "DECRETO DE NECESIDAD Y URGENCIA - DNU - 70/2023" / "DECRETO 70/23" / "DNU 179/25"
_DNU_REF_RE = re.compile(
    r"(?:DECRETO(?:\s+DE\s+NECESIDAD\s+Y\s+URGENCIA)?|DNU)[^0-9]{0,20}"
    r"(?P<numero>\d{1,5})\s*"
    r"(?:/\s*(?P<anio_corto>\d{2,4})|DEL?\b[^0-9]*\d{1,2}\s+DE\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+\s+DE\s+(?P<anio_largo>\d{4}))?",
    re.IGNORECASE,
)


@dataclass(slots=True)
class DictamenBicameral:
    expediente_hcdn: str  # == PROYECTO_ID == norma.external_id (hcdn_proyectos)
    giro: str
    tipo: str | None  # "Orden del Día" | ...
    observaciones: str | None
    numero_od: str | None
    fecha: Date | None

    def veredicto(self) -> str | None:
        """Sentido del dictamen de mayoría: 'validez' | 'invalidez' | None."""
        obs = (self.observaciones or "").upper()
        if not obs:
            return None
        # Si hay dictamen de mayoría y minoría, el de mayoría manda.
        mayoria = obs.split("DICTAMEN DE MINORIA")[0]
        # "ACONSEJA ... DECLARAR LA INVALIDEZ" / "APROBANDO LA VALIDEZ" / "RECHAZO"
        if re.search(r"\bINVALIDEZ\b|\bRECHAZ", mayoria):
            return "invalidez"
        if re.search(r"\bVALIDEZ\b|\bAPROBA", mayoria):
            return "validez"
        return None


def parse_dnu_ref(texto: str | None) -> tuple[int, int | None] | None:
    """Extrae (numero, anio) del DNU referenciado en un texto. None si no hay."""
    if not texto:
        return None
    m = _DNU_REF_RE.search(texto)
    if not m:
        return None
    numero = int(m.group("numero"))
    anio_raw = m.group("anio_corto") or m.group("anio_largo")
    anio: int | None = None
    if anio_raw:
        anio = int(anio_raw)
        if anio < 100:  # "70/23" -> 2023; "897/07" -> 2007 (no hay DNUs pre-1994 con /YY)
            anio += 2000 if anio < 70 else 1900
    return numero, anio


def _parse_fecha(value: str | None) -> Date | None:
    v = (value or "").strip()
    if not v or v.upper() == "NA":
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "")).date()
    except ValueError:
        return None


def _na(value: str | None) -> str | None:
    v = (value or "").strip()
    return None if not v or v.upper() == "NA" else v


def iter_dictamenes_bicameral(csv_path: Path) -> Iterator[DictamenBicameral]:
    """Itera los dictámenes de la Bicameral DNU desde el CSV de HCDN en disco."""
    with csv_path.open("rb") as binary:
        text = io.TextIOWrapper(binary, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.DictReader(text)
        for row in reader:
            giro = (row.get("GIRO") or "").upper()
            if _GIRO_BICAMERAL not in giro:
                continue
            expediente = (row.get("EXPEDIENTE") or "").strip()
            if not expediente:
                continue
            yield DictamenBicameral(
                expediente_hcdn=expediente,
                giro=giro,
                tipo=_na(row.get("TIPO")),
                observaciones=_na(row.get("OBSERVACIONES")),
                numero_od=_na(row.get("NUMERO")),
                fecha=_parse_fecha(row.get("FECHA")),
            )
