"""Legislatura de la Ciudad de Buenos Aires — expedientes parlamentarios.

No hay API documentada ni datos abiertos vigentes. El buscador oficial
(https://parlamentaria.legislatura.gob.ar/pages/expedientes.aspx) consulta un
web service ASMX que devuelve XML; es el mismo que usamos acá:

- ``POST /webservices/Json.asmx/GetExpedienteAvanzada``
  (``application/x-www-form-urlencoded``). Filtra por fecha de INICIO del
  expediente (``FechaDesde``/``FechaHasta`` en dd/mm/aaaa); el resto de los
  parámetros van vacíos. Devuelve el estado ACTUAL de cada expediente, así que
  re-consultar una ventana vieja actualiza estado y sanción.

  Respuesta::

    <ArrayOfExpedienteAvanzado xmlns="http://tempuri.org/">
      <expedienteAvanzado>
        <id_expediente>143054</id_expediente>
        <nro_de_expediente>3425-D-2026</nro_de_expediente>
        <fch_inicio>30/10/2026 16:35:03</fch_inicio>
        <autor_des>GONZÁLEZ, ANDREA MARIANA</autor_des>
        <coautores_des>BIELLI, MARÍA; …</coautores_des>
        <tipo_proyecto_des>LEY</tipo_proyecto_des>
        <fch_movimiento>3/11/2026 14:40:56</fch_movimiento>
        <ubicacion_des>MEP</ubicacion_des>
        <descripcion>ESPERANDO ENVIO A COMISION (ESPERANDO RECEPCION)</descripcion>
        <TieneSancion>0</TieneSancion>
        <sumario>SISTEMA INTEGRAL DE …</sumario>
        <urlDoc>228310</urlDoc>
      </expedienteAvanzado>
    </ArrayOfExpedienteAvanzado>

Detalle: ``/pages/expediente.aspx?id={id_expediente}``; PDF del proyecto:
``/pages/download.aspx?IdDoc={urlDoc}``. Al no estar documentado puede cambiar
sin aviso: los tests fijan el formato con un fixture real.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime, timedelta
from typing import Self

from vigia_connectors._http import make_client

LEGISLATURA_BASE = "https://parlamentaria.legislatura.gob.ar"
USER_AGENT = "vigia-cesba/0.1 (+https://www.cesba.gob.ar)"
_NS = {"t": "http://tempuri.org/"}

# Ventana por consulta. El servicio no pagina: con ventanas cortas nunca nos
# acercamos al tope (~1.000) y si una viene llena se parte en dos.
_VENTANA_DIAS = 7
_TOPE_SOSPECHOSO = 900

# Origen del expediente según la letra del número ("3425-D-2026").
ORIGENES = {
    "D": "Diputados/as",
    "J": "Poder Ejecutivo",
    "E": "Entidades",
    "P": "Particulares",
    "O": "Organismos oficiales",
    "F": "Fiscalía / Ministerio Público",
    "N": "Notas",
}

# Tipos que son proyectos propiamente dichos → "Proyecto de ley", etc.
_PROYECTOS = {"LEY", "RESOLUCION", "RESOLUCIÓN", "DECLARACION", "DECLARACIÓN", "DECRETO"}


def _parse_dt(s: str | None) -> datetime | None:
    """'30/10/2026 16:35:03' o '3/11/2026 14:40:56' → datetime (hora local)."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _split(s: str | None, sep: str) -> list[str]:
    return [p.strip() for p in (s or "").split(sep) if p.strip()]


@dataclass
class Expediente:
    id_expediente: int
    numero: str                 # "3425-D-2026"
    fecha_inicio: datetime | None
    fecha_movimiento: datetime | None
    tipo: str                   # "LEY", "RESOLUCION", "ESCUELAS", …
    sumario: str
    autor: str | None
    autor_id: str | None
    coautores: list[str]
    ubicacion: str | None
    estado: str | None
    sancionado: bool
    id_documento: int | None

    @property
    def origen(self) -> str | None:
        partes = self.numero.split("-")
        return ORIGENES.get(partes[1], partes[1]) if len(partes) == 3 else None

    @property
    def tipo_nombre(self) -> str:
        """Etiqueta legible del tipo: 'Proyecto de ley', 'Escuelas', …"""
        t = self.tipo.strip().upper()
        if t in _PROYECTOS:
            return "Proyecto de " + t.lower().replace("resolucion", "resolución").replace("declaracion", "declaración")
        return t.capitalize()

    @property
    def url(self) -> str:
        return f"{LEGISLATURA_BASE}/pages/expediente.aspx?id={self.id_expediente}"

    @property
    def url_documento(self) -> str | None:
        return f"{LEGISLATURA_BASE}/pages/download.aspx?IdDoc={self.id_documento}" if self.id_documento else None

    def detect_sector(self) -> str | None:
        from vigia_connectors.sectores import detect_sector

        return detect_sector(self.sumario)


def parse_expedientes(xml: str | bytes) -> list[Expediente]:
    """Parsea la respuesta XML de GetExpedienteAvanzada."""
    root = ET.fromstring(xml)
    out: list[Expediente] = []
    for e in root.findall("t:expedienteAvanzado", _NS):
        def txt(tag: str) -> str | None:
            v = e.findtext(f"t:{tag}", namespaces=_NS)
            return v.strip() if v and v.strip() else None

        numero = txt("nro_de_expediente")
        id_exp = txt("id_expediente")
        if not numero or not id_exp:
            continue
        doc = txt("urlDoc")
        out.append(
            Expediente(
                id_expediente=int(id_exp),
                numero=numero,
                fecha_inicio=_parse_dt(txt("fch_inicio")),
                fecha_movimiento=_parse_dt(txt("fch_movimiento")),
                tipo=txt("tipo_proyecto_des") or "OTRO",
                sumario=txt("sumario") or f"Expediente {numero}",
                autor=txt("autor_des"),
                autor_id=txt("autor_id"),
                coautores=_split(txt("coautores_des"), ";"),
                ubicacion=txt("ubicacion_des"),
                estado=txt("descripcion"),
                sancionado=txt("TieneSancion") == "1",
                id_documento=int(doc) if doc and doc.isdigit() and int(doc) > 0 else None,
            )
        )
    return out


class LegislaturaClient:
    """Cliente async del web service de expedientes de la Legislatura."""

    def __init__(self, *, timeout: float = 60.0) -> None:
        self._client = make_client(
            base_url=LEGISLATURA_BASE,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _avanzada(self, desde: Date, hasta: Date) -> list[Expediente]:
        resp = await self._client.post(
            "/webservices/Json.asmx/GetExpedienteAvanzada",
            data={
                "IdProyectoTipo": "", "IdAutoresInternos": "", "IdUbicacion": "",
                "IdEstado": "", "Sumario": "", "SumarioExacto": "0",
                "FechaDesde": desde.strftime("%d/%m/%Y"),
                "FechaHasta": hasta.strftime("%d/%m/%Y"),
                "AnioParlamentario": "", "Limite": "",
            },
        )
        resp.raise_for_status()
        return parse_expedientes(resp.content)

    async def fetch_rango(self, desde: Date, hasta: Date) -> list[Expediente]:
        """Expedientes iniciados entre `desde` y `hasta` (inclusive), en ventanas cortas.

        Si una ventana devuelve una cantidad sospechosa de cerca del tope del
        servicio, se parte en dos para no perder expedientes.
        """
        out: dict[str, Expediente] = {}
        pendientes: list[tuple[Date, Date]] = []
        d = desde
        while d <= hasta:
            fin = min(hasta, d + timedelta(days=_VENTANA_DIAS - 1))
            pendientes.append((d, fin))
            d = fin + timedelta(days=1)
        while pendientes:
            a, b = pendientes.pop(0)
            lote = await self._avanzada(a, b)
            if len(lote) >= _TOPE_SOSPECHOSO and a < b:
                medio = a + (b - a) // 2
                pendientes[:0] = [(a, medio), (medio + timedelta(days=1), b)]
                continue
            for e in lote:
                out[e.numero] = e
        return list(out.values())
