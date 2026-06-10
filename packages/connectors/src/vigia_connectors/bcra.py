"""BCRA — Comunicaciones "A" (normativa cambiaria y financiera).

Port del conector de InvestArg adaptado a Vigía. Las Comunicaciones A son el
instrumento normativo principal del BCRA (acceso al MULC, encajes, deuda
comercial, etc.). Cada una es un PDF en
``bcra.gob.ar/Pdfs/comytexord/A{num}.pdf`` (301 → /archivos/...; verificado
2026-06: los números inexistentes devuelven 404 con un HTML placeholder).

Estrategia: numeración secuencial → se sondea desde un cursor (el máximo ya
ingestado) hacia adelante; el texto se extrae con pypdf (si el PDF es escaneado
y rinde <100 chars, va solo el título — el FTS por título sigue sirviendo).
"""
from __future__ import annotations

import asyncio
import io
import re
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from typing import AsyncIterator, Self

import httpx
from pypdf import PdfReader

from vigia_connectors._http import make_client

BCRA_PDF_BASE = "https://www.bcra.gob.ar/Pdfs/comytexord"

# Los 404 devuelven un HTML placeholder (~62KB); las Comunicaciones reales son PDFs.
_PLACEHOLDER_BYTES_MIN = 64_000

_RE_REF = re.compile(r"Ref\.?:\s*(?:Circular\s+)?(.+?)(?:\n|$)", re.IGNORECASE)
_RE_DATE = re.compile(r"COMUNICACI.N\s+\"?[“A”]\"?\s*(\d{3,5})\s+(\d{1,2}/\d{1,2}/\d{4})")
_RE_DATE_LOOSE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")
_RE_SPACES = re.compile(r"\s+")


@dataclass(slots=True)
class ComunicacionBcra:
    serie: str  # "A" (normativas); "B" operativas quedan fuera de v1
    numero: int
    fecha: Date | None
    titulo: str
    body: str | None
    url: str

    @property
    def external_id(self) -> str:
        return f"{self.serie}{self.numero}"

    def detect_sector(self) -> str | None:
        from vigia_connectors.sectores import detect_sector

        return detect_sector(self.titulo, (self.body or "")[:2000]) or "Economía"


def _clean_mojibake(s: str) -> str:
    return s.replace("�", "")


def _parse_first_page(text: str) -> tuple[str, Date | None]:
    """Extrae (título, fecha) de la primera página del PDF (bloque "Ref.:")."""
    code_line = ""
    subject_lines: list[str] = []
    m = _RE_REF.search(text)
    if m:
        idx = text.find(m.group(0)) + len(m.group(0))
        slice_ = text[idx : idx + 1500]
        for raw in slice_.splitlines():
            line = raw.strip()
            if not line:
                if subject_lines:
                    break
                continue
            if line.startswith(("___", "---", "===")):
                break
            looks_like_code = line.endswith(":") and not re.search(r"[a-z]", line) and len(line) < 80
            if looks_like_code and not subject_lines:
                code_line = line.rstrip(":").strip()
                continue
            subject_lines.append(line)
            if sum(len(s) for s in subject_lines) > 240:
                break

    subject = " ".join(subject_lines).strip(" .:")
    parts = [p for p in (code_line, subject) if p]
    title = _clean_mojibake(_RE_SPACES.sub(" ", " — ".join(parts)))
    title = title[:240] if title else "Comunicación A"

    fecha = None
    m_date = _RE_DATE.search(text)
    if m_date:
        try:
            fecha = datetime.strptime(m_date.group(2), "%d/%m/%Y").date()
        except ValueError:
            fecha = None
    else:
        m_loose = _RE_DATE_LOOSE.search(text[:600])
        if m_loose:
            try:
                fecha = datetime.strptime(m_loose.group(1), "%d/%m/%Y").date()
            except ValueError:
                fecha = None
    return title, fecha


def _extract_text(pdf_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return ""
    pages: list[str] = []
    for page in reader.pages[:50]:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(pages)


class BcraClient:
    def __init__(self, *, serie: str = "A", concurrency: int = 6, timeout: float = 30.0) -> None:
        self.serie = serie
        self._client = make_client(base_url=BCRA_PDF_BASE, timeout=timeout)
        self._sem = asyncio.Semaphore(concurrency)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _fetch_pdf(self, num: int) -> bytes | None:
        async with self._sem:
            try:
                resp = await self._client.get(f"/{self.serie}{num}.pdf")
            except httpx.HTTPError:
                return None
        if resp.status_code != 200:
            return None
        content = resp.content
        if len(content) < _PLACEHOLDER_BYTES_MIN or not content.startswith(b"%PDF"):
            return None
        return content

    async def exists(self, num: int) -> bool:
        return await self._fetch_pdf(num) is not None

    async def find_latest_number(self, *, start: int = 8700, lookback: int = 600) -> int | None:
        """Busca el último número publicado sondeando hacia atrás en tandas."""
        num = start
        while num > start - lookback:
            chunk = list(range(num, max(num - 20, start - lookback), -1))
            results = await asyncio.gather(*(self.exists(n) for n in chunk))
            for n, ok in zip(chunk, results):
                if ok:
                    return n
            num -= 20
        return None

    async def fetch(self, num: int) -> ComunicacionBcra | None:
        pdf = await self._fetch_pdf(num)
        if pdf is None:
            return None
        text = _extract_text(pdf)
        title, fecha = _parse_first_page(text[:4000])
        body_clean = _clean_mojibake(text) if text else ""
        body = body_clean if len(body_clean) >= 100 else None
        return ComunicacionBcra(
            serie=self.serie,
            numero=num,
            fecha=fecha,
            titulo=title,
            body=body,
            url=f"{BCRA_PDF_BASE}/{self.serie}{num}.pdf",
        )

    async def iter_desde(self, cursor: int, *, max_gap: int = 10) -> AsyncIterator[ComunicacionBcra]:
        """Comunicaciones nuevas a partir de cursor+1, hasta max_gap misses seguidos.

        La numeración es secuencial pero puede haber huecos chicos (anuladas).
        """
        num = cursor + 1
        misses = 0
        while misses < max_gap:
            c = await self.fetch(num)
            if c is None:
                misses += 1
            else:
                misses = 0
                yield c
            num += 1

    async def iter_recent(self, *, start_number: int, count: int = 300) -> AsyncIterator[ComunicacionBcra]:
        """Hasta `count` Comunicaciones hacia atrás desde start_number (backfill)."""
        seen = 0
        num = start_number
        while seen < count and num > 0:
            chunk = list(range(num, max(num - 20, 0), -1))
            results = await asyncio.gather(*(self.fetch(n) for n in chunk))
            for r in results:
                if r is not None:
                    yield r
                    seen += 1
                    if seen >= count:
                        return
            num -= 20
