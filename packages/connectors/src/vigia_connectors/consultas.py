"""Consultas públicas — consultapublica.argentina.gob.ar (DemocracyOS).

Señal regulatoria temprana: anteproyectos y reglamentos en consulta ANTES de
ser norma. La plataforma es un DemocracyOS con API pública (verificado 2026-06):

- ``GET /api/forum/all?page=N`` (Accept: application/json) — cada "forum" es
  una consulta, paginado de a 20. ``extra`` trae el organismo convocante,
  ``closingAt`` (cierre) y ``richSummary`` (HTML).

Volumen ínfimo (~5-15/mes): se re-scrapea todo en cada corrida y el upsert
flipea el estado Abierta→Cerrada solo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime, timezone
from typing import Self

from vigia_connectors._http import get_json, make_client

CONSULTAS_BASE = "https://consultapublica.argentina.gob.ar"
USER_AGENT = "vigia/0.1 (+https://vigia.openarg.org)"

_TAG_RE = re.compile(r"<[^>]+>")
_MAX_PAGES = 30  # backstop: ~600 consultas; hoy hay <100


def _strip_html(html: str | None) -> str | None:
    if not html:
        return None
    text = _TAG_RE.sub(" ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _parse_iso_date(value: str | None) -> Date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


@dataclass(slots=True)
class ConsultaPublica:
    forum_id: str
    name: str  # slug
    titulo: str
    resumen: str | None
    organismo: str | None
    fecha_creacion: Date | None
    fecha_cierre: Date | None

    @property
    def url(self) -> str:
        return f"{CONSULTAS_BASE}/{self.name}"

    def estado(self, hoy: Date | None = None) -> str:
        hoy = hoy or datetime.now(timezone.utc).date()
        if self.fecha_cierre is not None and self.fecha_cierre < hoy:
            return "Cerrada"
        return "Abierta"

    def detect_sector(self) -> str | None:
        from vigia_connectors.sectores import detect_sector

        return detect_sector(self.titulo, self.organismo, self.resumen)


def parse_forum(f: dict) -> ConsultaPublica | None:
    forum_id = (f.get("id") or "").strip()
    titulo = (f.get("title") or "").strip()
    if not forum_id or not titulo:
        return None
    extra = f.get("extra") or {}
    resumen = _strip_html(extra.get("richSummary")) or (f.get("summary") or "").strip() or None
    return ConsultaPublica(
        forum_id=forum_id,
        name=(f.get("name") or forum_id).strip(),
        titulo=titulo,
        resumen=resumen[:2000] if resumen else None,
        organismo=(extra.get("owner") or "").strip() or None,
        fecha_creacion=_parse_iso_date(f.get("createdAt")),
        fecha_cierre=_parse_iso_date(extra.get("closingAt")),
    )


class ConsultasClient:
    def __init__(self, *, timeout: float = 30.0) -> None:
        self._client = make_client(
            base_url=CONSULTAS_BASE,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch_all(self) -> list[ConsultaPublica]:
        """Todas las consultas públicas (paginado de a 20, hasta agotar).

        OJO: la paginación de DemocracyOS es 0-INDEXED (page=1 es la SEGUNDA
        página — verificado contra la API; arrancar en 1 saltea las 20 más
        recientes).
        """
        out: list[ConsultaPublica] = []
        for page in range(0, _MAX_PAGES):
            data = await get_json(self._client, f"/api/forum/all?page={page}")
            if not isinstance(data, list) or not data:
                break
            for f in data:
                c = parse_forum(f)
                if c is not None and (f.get("visibility") or "public") == "public":
                    out.append(c)
            if len(data) < 20:
                break
        return out
