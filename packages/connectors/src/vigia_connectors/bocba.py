"""BOCBA — Boletín Oficial de la Ciudad de Buenos Aires.

API REST pública (sin autenticación):
  https://api-restboletinoficial.buenosaires.gob.ar

Endpoints usados:

- ``GET /obtenerBoletin/{fecha|numero}/false``
  Devuelve JSON con metadata del boletín + normas agrupadas por
  sección → tipo → organismo. El parámetro ``false`` indica que
  no se incluyen los textos completos (suficiente para ingesta).

  Respuesta::

    {
      "boletin": {
        "fecha_publicacion": "18/06/2026",
        "numero": 7390,
        "url_boletin": "https://api-restboletinoficial.buenosaires.gob.ar/download/5149088"
      },
      "secciones": [ { "superseccion_id": 1, "nombre": "...", "url_documento": "..." } ],
      "normas": {
        "Poder Ejecutivo": {
          "Resolución": {
            "Ministerio de Salud GCBA": [
              {
                "nombre": "Resolución N° 2349/MSGC/26",
                "sumario": "Asigna suplemento de gabinete...",
                "id_norma": 5149085,
                "url_norma": "https://api-restboletinoficial.buenosaires.gob.ar/download/5149085",
                "id_sdin": "...",
                "anexos": [ { "nombre_anexo": "...", "filenet_firmado": "..." } ]
              }
            ]
          }
        }
      }
    }

- ``GET /obtenerFiltrosDeBusqueda`` — catálogo de secciones y tipos (bootstrap).

Los archivos individuales (PDF/XML) están en:
  https://documentosboletinoficial.buenosaires.gob.ar/publico/{nombre}

No se usa scraping HTML: la API estructurada provee todo lo necesario.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date as Date
from datetime import datetime
from typing import Any, Self

from vigia_connectors._http import get_json, make_client

BOCBA_API = "https://api-restboletinoficial.buenosaires.gob.ar"
USER_AGENT = "vigia/0.1 (+https://vigia.openarg.org)"

# "Resolución N° 2349/MSGC/26" → número "2349/MSGC/26"
_NUMERO_RE = re.compile(r"N[°º]\s*(?P<numero>[\d][^\s,]+)", re.IGNORECASE)

# Secciones del BOCBA y su mapeo a etiquetas internas
_SECCION_MAP: dict[str, str] = {
    "Poder Legislativo": "legislativo",
    "Poder Ejecutivo": "ejecutivo",
    "Poder Judicial": "judicial",
    "Órganos de Control": "control",
    "Comunicados y Avisos": "avisos",
    "Licitaciones": "licitaciones",
    "Edictos Oficiales": "edictos_oficiales",
    "Edictos Particulares": "edictos_particulares",
    "Fuera de Nivel": "fuera_de_nivel",
    "Trimestrales": "trimestrales",
}

# Tipos de norma del BOCBA → slugs internos de Vigía
_TIPO_SLUG_MAP: dict[str, str] = {
    "decreto": "DECRETO",
    "ley": "LEY",
    "resolución": "RESOLUCION",
    "resolucion": "RESOLUCION",
    "disposición": "DISPOSICION",
    "disposicion": "DISPOSICION",
    "acta": "OTRA",
    "circular": "OTRA",
    "convenio": "OTRA",
    "resolución comunal": "RESOLUCION",
    "resolución de directorio": "RESOLUCION",
}


def _parse_fecha(s: str) -> Date | None:
    """Parsea 'dd/mm/yyyy' → date, o None si falla."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


@dataclass(slots=True)
class BocbaNorma:
    """Representa una norma del Boletín Oficial de la Ciudad de Buenos Aires."""

    id_norma: int
    numero_boletin: int
    fecha: Date
    seccion: str          # etiqueta interna (ej. "ejecutivo")
    seccion_nombre: str   # nombre original (ej. "Poder Ejecutivo")
    tipo_nombre: str      # nombre original (ej. "Resolución")
    organismo: str        # repartición emisora
    nombre: str           # "Resolución N° 2349/MSGC/26"
    sumario: str | None
    url_norma: str
    id_sdin: str | None = None
    anexos: list[dict[str, str]] = field(default_factory=list)

    @property
    def numero(self) -> str | None:
        m = _NUMERO_RE.search(self.nombre)
        return m.group("numero") if m else None

    def tipo_slug(self) -> str:
        key = self.tipo_nombre.strip().lower()
        for prefix, slug in _TIPO_SLUG_MAP.items():
            if key.startswith(prefix):
                return slug
        return "OTRA"

    def detect_sector(self) -> str | None:
        from vigia_connectors.sectores import detect_sector
        return detect_sector(self.organismo, self.nombre, self.sumario)


def _iter_normas(
    normas_raw: dict[str, Any],
    numero_boletin: int,
    fecha: Date,
) -> list[BocbaNorma]:
    """Aplana la estructura anidada {sección → tipo → organismo → [normas]}."""
    result: list[BocbaNorma] = []
    for seccion_nombre, tipos in normas_raw.items():
        seccion = _SECCION_MAP.get(seccion_nombre, "otra")
        if not isinstance(tipos, dict):
            continue
        for tipo_nombre, organismos in tipos.items():
            if not isinstance(organismos, dict):
                continue
            for organismo, items in organismos.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    id_norma = item.get("id_norma")
                    if not id_norma:
                        continue
                    result.append(
                        BocbaNorma(
                            id_norma=int(id_norma),
                            numero_boletin=numero_boletin,
                            fecha=fecha,
                            seccion=seccion,
                            seccion_nombre=seccion_nombre,
                            tipo_nombre=tipo_nombre,
                            organismo=organismo,
                            nombre=item.get("nombre", ""),
                            sumario=item.get("sumario") or None,
                            url_norma=item.get("url_norma", ""),
                            id_sdin=item.get("id_sdin") or None,
                            anexos=item.get("anexos") or [],
                        )
                    )
    return result


class BocbaClient:
    """Cliente async para la API del Boletín Oficial de la CABA."""

    def __init__(self, *, timeout: float = 30.0) -> None:
        self._client = make_client(
            base_url=BOCBA_API,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch_boletin(
        self, fecha: Date | None = None, numero: int | None = None
    ) -> list[BocbaNorma]:
        """Normas del boletín para una fecha o número dado (default: hoy).

        Si el día no tiene boletín (feriado / fin de semana) la API devuelve
        ``{"errores": [...]}`` → se retorna lista vacía.
        """
        if numero is not None:
            parametro = str(numero)
        else:
            d = fecha or Date.today()
            parametro = d.strftime("%d-%m-%Y")

        # carga_datos=true trae el JSON completo con normas;
        # carga_datos=false solo devuelve metadata del boletín (sin normas).
        data: Any = await get_json(self._client, f"/obtenerBoletin/{parametro}/true")

        if not isinstance(data, dict) or "errores" in data:
            return []

        boletin = data.get("boletin", {})
        numero_boletin: int = int(boletin.get("numero", 0))
        fecha_str: str = boletin.get("fecha_publicacion", "")
        fecha_boletin: Date = _parse_fecha(fecha_str) or fecha or Date.today()

        normas_raw = data.get("normas", {})
        # La API anida el dict de normas bajo una clave "normas" extra: {"normas": {...}}
        if isinstance(normas_raw, dict) and "normas" in normas_raw:
            normas_raw = normas_raw["normas"]

        return _iter_normas(normas_raw, numero_boletin, fecha_boletin)

    async def fetch_filtros(self) -> dict[str, Any]:
        """Catálogo de secciones y tipos de norma disponibles."""
        return await get_json(self._client, "/obtenerFiltrosDeBusqueda")
