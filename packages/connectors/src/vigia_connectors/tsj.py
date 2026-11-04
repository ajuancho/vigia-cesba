"""Tribunal Superior de Justicia de la CABA — sentencias y resoluciones.

Fuente: el buscador oficial de jurisprudencia (ASP clásico, sin API):

- ``GET  http://jurisprudencia.tsjbaires.gob.ar/jurisprudencia/`` abre sesión.
- ``POST .../jurisprudencia/resultadoBusqueda.asp`` con el formulario de
  búsqueda: rango de fecha de sentencia (``expFechaResDesde``/``Hasta``,
  dd/mm/aaaa), todas las secretarías tildadas, ``pag`` y ``cantRegPagina``
  (hasta 100). Devuelve una tabla HTML.

Cada resolución trae número de expediente, carátula, secretaría, fecha, los
términos del tesauro y un link al PDF:
``https://www.tsjbaires.gov.ar/components/com_expedientes/expedientes_download_EJE.php
?expediente=…&anio=…&incidente=…&movimiento=…``.

El HTML declara ISO-8859-1 pero el contenido viene en UTF-8. Publica con unos
días de atraso respecto de la fecha de la sentencia. Los datos abiertos del
TSJ (datos.tsjbaires.gob.ar, CSV desde 2016) quedan como respaldo histórico.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import date as Date
from datetime import timedelta
from typing import Self

from vigia_connectors._http import make_client

TSJ_BUSCADOR = "http://jurisprudencia.tsjbaires.gob.ar"
TSJ_DESCARGA = "https://www.tsjbaires.gov.ar/components/com_expedientes"
USER_AGENT = "vigia-cesba/0.1 (+https://www.cesba.gob.ar)"
POR_PAGINA = 100
_VENTANA_DIAS = 31

SECRETARIAS = {
    "SAOyRC": "Asuntos Originarios y Relaciones con la Comunidad",
    "SAPPJCyF": "Asuntos Penales, Penales Juveniles, Contravencionales y de Faltas",
    "SACAyT": "Asuntos Contencioso Administrativos y Tributarios",
    "SACyC": "Asuntos Civiles y Comerciales",
    "SAL": "Asuntos Laborales",
    "SAG": "Asuntos Generales",
    "TSN": "Tribunal de Superintendencia del Notariado",
}

# Checkboxes de secretarías del formulario (todas tildadas = sin filtro).
_CHECKS = ("chkSAO", "chkSACAYT", "chkSAC", "chkSACyC", "chkSAL", "chkSAG", "chkTSN")

_FILA_RE = re.compile(
    r'class="resultadoFila\w+Dest"><b>\d+\.</b></td>\s*'
    r'<td[^>]*><b>(?P<expediente>[^<]*)</b></td>\s*'
    r'<td[^>]*><b>(?P<caratula>.*?)</b></td>\s*'
    r'<td[^>]*title="(?P<secretaria>[^"]*)"[^>]*>.*?</td>\s*'
    r'<td[^>]*>(?P<fecha>\d{1,2}/\d{1,2}/\d{4})</td>'
    r'(?P<resto>.*?)(?=class="resultadoFila\w+Dest"|</table>\s*<table|\Z)',
    re.S,
)
_PDF_RE = re.compile(r"downloadPDF\('(\w+)',\s*'(\d+)',\s*'(\d+)',\s*'(\d+)',\s*'(\d+)'\)")
_TESAURO_RE = re.compile(r"busqPorTerminoTesauro\('\d+',\s*'([^']*)'\)")
_TOTAL_RE = re.compile(r"Se encontraron\s+(\d+)\s+resultado")


@dataclass
class Sentencia:
    expediente: str
    caratula: str
    secretaria: str              # sigla: "SAL", "SACyC", …
    fecha: Date
    origen: str | None = None    # "EJE"
    incidente: str | None = None
    movimiento: str | None = None
    anio: str | None = None
    tesauro: list[str] = field(default_factory=list)

    @property
    def external_id(self) -> str:
        """Única por resolución: un expediente tiene varios movimientos."""
        return f"{self.expediente}-{self.incidente or 0}-{self.movimiento or self.fecha.isoformat()}"

    @property
    def secretaria_nombre(self) -> str:
        return SECRETARIAS.get(self.secretaria, self.secretaria)

    @property
    def url_pdf(self) -> str | None:
        if not self.movimiento:
            return None
        script = "expedientes_download_EJE.php" if self.origen == "EJE" else "expedientes_download.php"
        return (
            f"{TSJ_DESCARGA}/{script}?expediente={self.expediente}&anio={self.anio}"
            f"&incidente={self.incidente}&movimiento={self.movimiento}"
        )

    def detect_sector(self) -> str | None:
        from vigia_connectors.sectores import detect_sector

        return detect_sector(self.caratula, " ".join(self.tesauro))


def _texto(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse_resultados(page: str) -> tuple[list[Sentencia], int | None]:
    """Filas de una página de resultados + total informado por el buscador."""
    total = _TOTAL_RE.search(_texto(page))
    out: list[Sentencia] = []
    for m in _FILA_RE.finditer(page):
        d, mth, y = m.group("fecha").split("/")
        s = Sentencia(
            expediente=_texto(m.group("expediente")),
            caratula=_texto(m.group("caratula")),
            secretaria=_texto(m.group("secretaria")),
            fecha=Date(int(y), int(mth), int(d)),
        )
        pdf = _PDF_RE.search(m.group("resto"))
        if pdf:
            s.origen, _, s.incidente, s.movimiento, s.anio = pdf.groups()
        s.tesauro = [html.unescape(t).strip() for t in _TESAURO_RE.findall(m.group("resto")) if t.strip()]
        out.append(s)
    return out, int(total.group(1)) if total else None


class TsjClient:
    """Cliente async del buscador de jurisprudencia del TSJ."""

    def __init__(self, *, timeout: float = 90.0) -> None:
        self._client = make_client(base_url=TSJ_BUSCADOR, timeout=timeout, headers={"User-Agent": USER_AGENT})
        self._sesion = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _pagina(self, desde: Date, hasta: Date, pag: int) -> tuple[list[Sentencia], int | None]:
        if not self._sesion:
            (await self._client.get("/jurisprudencia/")).raise_for_status()
            self._sesion = True
        resp = await self._client.post(
            "/jurisprudencia/resultadoBusqueda.asp",
            data={
                "post": "1", "pag": str(pag), "cantRegPagina": str(POR_PAGINA),
                "expFechaResDesde": desde.strftime("%d/%m/%Y"),
                "expFechaResHasta": hasta.strftime("%d/%m/%Y"),
                **{c: "on" for c in _CHECKS},
            },
        )
        resp.raise_for_status()
        # Declara ISO-8859-1 pero el contenido está en UTF-8.
        return parse_resultados(resp.content.decode("utf-8", "replace"))

    async def fetch_rango(self, desde: Date, hasta: Date) -> list[Sentencia]:
        """Resoluciones con fecha entre `desde` y `hasta`, en ventanas mensuales paginadas."""
        out: dict[str, Sentencia] = {}
        d = desde
        while d <= hasta:
            fin = min(hasta, d + timedelta(days=_VENTANA_DIAS - 1))
            pag = 1
            while True:
                filas, total = await self._pagina(d, fin, pag)
                for s in filas:
                    out[s.external_id] = s
                if not filas or total is None or pag * POR_PAGINA >= total:
                    break
                pag += 1
            d = fin + timedelta(days=1)
        return list(out.values())
