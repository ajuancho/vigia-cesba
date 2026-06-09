"""InfoLEG / Boletín Oficial connector.

El Ministerio de Justicia publica un CSV consolidado con cada norma nacional
publicada en la primera sección del Boletín Oficial (leyes, decretos,
resoluciones, decisiones administrativas, etc.). Lo usamos en vez de scrapear
el BO directamente porque:
  - Es un dataset oficial, estable y estructurado.
  - Cada registro trae la fecha de publicación en el BO + edición + página.
  - Embebe la URL de InfoLEG, así el usuario puede ir al texto completo.

Source: https://datos.gob.ar/dataset/justicia-base-infoleg-normativa-nacional

Dos modos de ingesta:
- `fetch_sample()` — ~1000 registros (CSV ~730 KB). Útil para dev/demo.
- `iter_full_zip()` — generador streaming sobre el ZIP completo (~49 MB
  comprimido, ~500k registros desde 1853). Usar en producción con batching.
"""
from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from pathlib import Path
from typing import Self

from vigia_connectors._http import make_client

# "Muestreo" (sample) — CSV chico (~1000 registros, ~730KB) bueno para dev/demo.
INFOLEG_SAMPLE_URL = (
    "https://datos.jus.gob.ar/dataset/"
    "d9a963ea-8b1d-4ca3-9dd9-07a4773e8c23/resource/"
    "8b1c2310-564e-41e6-9a84-99cfa9939bbc/download/"
)

# ZIP completo (~49 MB comprimido). Contiene un CSV con el corpus entero.
INFOLEG_FULL_ZIP_URL = (
    "https://datos.jus.gob.ar/dataset/"
    "d9a963ea-8b1d-4ca3-9dd9-07a4773e8c23/resource/"
    "bf0ec116-ad4e-4572-a476-e57167a84403/download"
)


@dataclass(slots=True)
class InfoLegNorm:
    id_norma: str
    tipo_norma: str
    numero_norma: str | None
    clase_norma: str | None
    organismo_origen: str | None
    fecha_sancion: Date | None
    numero_boletin: str | None
    fecha_boletin: Date | None
    pagina_boletin: str | None
    titulo_resumido: str
    titulo_sumario: str | None
    texto_resumido: str | None
    texto_original_url: str | None

    def tipo_slug(self) -> str:
        """Normaliza tipo_norma al vocabulario de `norma.tipo` (Vigía)."""
        t = (self.tipo_norma or "").strip().lower()
        if t.startswith("decreto de necesidad") or "necesidad y urgencia" in t or t.startswith("dnu"):
            return "DNU"
        if t.startswith("ley"):
            return "LEY"
        if "decreto" in t:
            return "DECRETO"
        if t.startswith("resol"):
            return "RESOLUCION"
        if t.startswith("disposi"):
            return "DISPOSICION"
        if t.startswith("decisión administrativa") or t.startswith("decision administrativa"):
            return "DECRETO"  # decisión administrativa -> agrupada como acto del ejecutivo
        return "OTRA"

    def detect_sector(self) -> str | None:
        """Etiquetado barato de sector por organismo + keywords del título."""
        haystack = " ".join(
            filter(
                None,
                [self.organismo_origen, self.titulo_resumido, self.titulo_sumario, self.texto_resumido],
            )
        ).upper()
        rules = [
            ("Energía", ["VACA MUERTA", "PETRÓLEO", "PETROLEO", " GAS ", "GNL", "HIDROCARBURO", "ENERGIA", "ENERGÍA", "ENARGAS", "CAMMESA", "RENOVABLE"]),
            ("Minería", ["LITIO", "MINERIA", "MINERÍA", "MINERA ", "ORO", "COBRE", "SEGEMAR"]),
            ("Agro", ["AGROPECUAR", "GRANOS", "SENASA", "BIOECONOMIA", "BIOECONOMÍA", "GANADER"]),
            ("Tecnología", ["SOFTWARE", "ECONOMIA DEL CONOCIMIENTO", "ECONOMÍA DEL CONOCIMIENTO", "CIBERSEGURIDAD", "INTELIGENCIA ARTIFICIAL", "DATA CENTER"]),
            ("Economía", ["BCRA", "BANCO CENTRAL", "AFIP", "ARCA", "IMPOSITIV", "TRIBUTARI", "ADUANA", "FINANCIER"]),
            ("Salud", ["SALUD", "HOSPITAL", "MEDICAMENTO", "ANMAT", "SANITARI"]),
            ("Trabajo", ["TRABAJO", "SALARIO", "SMVM", "LABORAL", "EMPLEO", "ANSES", "ANSeS"]),
            ("Transporte", ["TRANSPORTE", "AUTOMOTOR", "AERONAUT", "FERROVIAR", "VIAL"]),
            ("Seguridad", ["SEGURIDAD", "POLICIA", "POLICÍA", "DEFENSA NACIONAL"]),
        ]
        for sector, keywords in rules:
            for kw in keywords:
                if kw in haystack:
                    return sector
        return None


def _parse_date(value: str) -> Date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class InfoLegClient:
    def __init__(self, *, timeout: float = 300.0) -> None:
        self._client = make_client(base_url="", timeout=timeout)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch_sample(self) -> list[InfoLegNorm]:
        """Descarga el CSV de muestreo (~1000 registros)."""
        resp = await self._client.get(INFOLEG_SAMPLE_URL)
        resp.raise_for_status()
        text = resp.content.decode("utf-8-sig", errors="replace")
        return list(self._parse_csv(text))

    async def download_full_zip(self, dest: Path) -> Path:
        """Stream del ZIP completo a disco. Devuelve el path."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with self._client.stream("GET", INFOLEG_FULL_ZIP_URL) as resp:
            resp.raise_for_status()
            with dest.open("wb") as fh:
                async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                    if chunk:
                        fh.write(chunk)
        return dest

    @staticmethod
    def iter_full_zip(zip_path: Path) -> Iterator[InfoLegNorm]:
        """Itera InfoLegNorm de a uno desde el ZIP completo en disco.

        Memory-friendly: solo vive en memoria la fila que se está parseando.
        Encoding: el archivo mezcla utf-8 BOM con latin-1 en registros viejos,
        por eso decodificamos con `errors="replace"`.
        """
        with zipfile.ZipFile(zip_path) as zf:
            csv_name = next(
                (
                    n
                    for n in zf.namelist()
                    if n.lower().endswith(".csv") and "modific" not in n.lower()
                ),
                None,
            )
            if csv_name is None:
                raise ValueError("No main CSV found inside InfoLEG ZIP")
            with zf.open(csv_name) as binary_stream:
                text_stream = io.TextIOWrapper(
                    binary_stream, encoding="utf-8-sig", errors="replace", newline=""
                )
                reader = csv.DictReader(text_stream)
                for row in reader:
                    norm = InfoLegClient._row_to_norm(row)
                    if norm is not None:
                        yield norm

    @staticmethod
    def _row_to_norm(row: dict) -> "InfoLegNorm | None":
        try:
            id_norma = (row.get("id_norma") or "").strip()
            if not id_norma:
                return None
            return InfoLegNorm(
                id_norma=id_norma,
                tipo_norma=(row.get("tipo_norma") or "").strip(),
                numero_norma=(row.get("numero_norma") or "").strip() or None,
                clase_norma=(row.get("clase_norma") or "").strip() or None,
                organismo_origen=(row.get("organismo_origen") or "").strip() or None,
                fecha_sancion=_parse_date(row.get("fecha_sancion", "")),
                numero_boletin=(row.get("numero_boletin") or "").strip() or None,
                fecha_boletin=_parse_date(row.get("fecha_boletin", "")),
                pagina_boletin=(row.get("pagina_boletin") or "").strip() or None,
                titulo_resumido=(row.get("titulo_resumido") or "").strip(),
                titulo_sumario=(row.get("titulo_sumario") or "").strip() or None,
                texto_resumido=(row.get("texto_resumido") or "").strip() or None,
                texto_original_url=(row.get("texto_original") or "").strip() or None,
            )
        except Exception:
            return None

    def _parse_csv(self, text: str):
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            norm = self._row_to_norm(row)
            if norm is not None:
                yield norm
