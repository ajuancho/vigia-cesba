"""Consultas de reportes compartidas entre la API (constructor) y los workers
(reportes programados).

Un reporte filtra `norma` por sección del boletín, tipo de procedimiento,
etapa, organismo, período y texto. Las licitaciones del BOCBA llegan con
`bora_seccion = 'Licitaciones'`: el tipo de procedimiento está en
`raw->>'tipo_nombre'` ("Licitación Obra Pública", "Contratación Menor", …) y la
etapa en el título ("Licitación Pública / Adjudicación  N° 1/AGMIG/26").
"""
from __future__ import annotations

import csv
import io
import json
from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import text

# Tipo de procedimiento / tipo de norma tal como lo publica el boletín.
TIPO_EXPR = "COALESCE(raw->>'tipo_nombre', tipo)"
# Etapa: en licitaciones sale del título ("<tipo> / <etapa>  N° …"); en los
# expedientes de la Legislatura es su estado de trámite (o "Sancionado"); en
# las sentencias del TSJ, el tema principal del tesauro (tipo de recurso).
ETAPA_EXPR = (
    "CASE WHEN bora_seccion = 'Tribunal Superior' THEN NULLIF(raw->>'tema_principal', '') "
    "WHEN bora_seccion = 'Legislatura' THEN "
    "CASE WHEN raw->>'sancionado' = 'true' THEN 'Sancionado' "
    r"ELSE NULLIF(btrim(regexp_replace(raw->>'estado', '\s*\(.*\)$', '')), '') END "
    r"ELSE NULLIF(btrim(substring(titulo from ' / ([^/]+?)\s+N[°º]')), '') END"
)

CSV_MAX = 20000        # tope de filas exportables
TOP_ORGANISMOS = 12

ORDEN_SQL = {
    "fecha_desc": "fecha_publicacion DESC NULLS LAST, id DESC",
    "fecha_asc": "fecha_publicacion ASC NULLS LAST, id ASC",
    "organismo": "organismo ASC NULLS LAST, fecha_publicacion DESC NULLS LAST",
    "tipo": f"{TIPO_EXPR} ASC, fecha_publicacion DESC NULLS LAST",
}

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")


def build_where(
    filtros: dict[str, Any],
    *,
    jurisdiccion: str | None = None,
    ingestado_desde: datetime | None = None,
) -> tuple[str, dict[str, Any]]:
    """WHERE + params para los filtros del constructor.

    `jurisdiccion`: scope fijo de la instancia (VIGIA_JURISDICCION_SCOPE).
    `ingestado_desde`: solo normas ingestadas después de ese instante (lo
    "nuevo desde el envío anterior" de un reporte programado).
    """
    conds: list[str] = []
    params: dict[str, Any] = {}
    for key, expr in (
        ("secciones", "bora_seccion"),
        ("tipos", TIPO_EXPR),
        ("etapas", ETAPA_EXPR),
        ("organismos", "organismo"),
    ):
        if filtros.get(key):
            conds.append(f"{expr} = ANY(:{key})")
            params[key] = list(filtros[key])
    if filtros.get("desde"):
        conds.append("fecha_publicacion >= :desde")
        params["desde"] = _as_date(filtros["desde"])
    if filtros.get("hasta"):
        conds.append("fecha_publicacion <= :hasta")
        params["hasta"] = _as_date(filtros["hasta"])
    texto = (filtros.get("texto") or "").strip()
    if texto:
        conds.append("search_vector @@ websearch_to_tsquery('spanish', :texto)")
        params["texto"] = texto
    if ingestado_desde is not None:
        conds.append("ingested_at > :_ingestado_desde")
        params["_ingestado_desde"] = ingestado_desde
    if jurisdiccion:
        conds.append("jurisdiccion = :_scope_jur")
        params["_scope_jur"] = jurisdiccion
    return ("WHERE " + " AND ".join(conds)) if conds else "", params


def _as_date(v: Any) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def filas_sql(where: str, orden: str) -> str:
    return f"""
        SELECT id, fecha_publicacion, {TIPO_EXPR} AS tipo, {ETAPA_EXPR} AS etapa,
               numero, titulo, resumen, organismo, url
        FROM norma {where}
        ORDER BY {ORDEN_SQL.get(orden, ORDEN_SQL['fecha_desc'])}
        LIMIT :_limit OFFSET :_offset
    """


def fila_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r[0], "fecha": r[1], "tipo": r[2], "etapa": r[3], "numero": r[4],
        "titulo": r[5], "objeto": r[6], "organismo": r[7], "url": r[8],
    }


async def agregados(session, where: str, params: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Total + agregados para gráficos (por mes, organismo, tipo y etapa)."""

    async def conteo(expr: str, limit: int | None = None) -> list[dict[str, Any]]:
        lim = f" LIMIT {int(limit)}" if limit else ""
        rows = (
            await session.execute(
                text(
                    f"SELECT v, c FROM (SELECT {expr} AS v, COUNT(*) c FROM norma {where} "
                    f"GROUP BY 1) t WHERE v IS NOT NULL ORDER BY c DESC{lim}"
                ),
                params,
            )
        ).all()
        return [{"valor": str(r[0]), "cantidad": int(r[1])} for r in rows]

    resumen = (
        await session.execute(
            text(
                f"SELECT COUNT(*), COUNT(DISTINCT organismo), MIN(fecha_publicacion), "
                f"MAX(fecha_publicacion) FROM norma {where}"
            ),
            params,
        )
    ).one()
    por_mes = (
        await session.execute(
            text(
                f"SELECT to_char(date_trunc('month', fecha_publicacion), 'YYYY-MM') m, COUNT(*) "
                f"FROM norma {where} {'AND' if where else 'WHERE'} fecha_publicacion IS NOT NULL "
                f"GROUP BY m ORDER BY m"
            ),
            params,
        )
    ).all()
    return int(resumen[0] or 0), {
        "por_mes": [{"valor": r[0], "cantidad": int(r[1])} for r in por_mes],
        "por_organismo": await conteo("organismo", TOP_ORGANISMOS),
        "por_tipo": await conteo(TIPO_EXPR, 20),
        "por_etapa": await conteo(ETAPA_EXPR, 10),
        "organismos_distintos": int(resumen[1] or 0),
        "desde": resumen[2],
        "hasta": resumen[3],
    }


def csv_text(filas: list[dict[str, Any]]) -> str:
    """CSV para Excel en es-AR: separador `;`, UTF-8 con BOM, fechas dd/mm/aaaa."""
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Fecha", "Tipo", "Etapa", "Número", "Título", "Objeto", "Organismo", "URL"])
    for f in filas:
        w.writerow([
            f["fecha"].strftime("%d/%m/%Y") if f["fecha"] else "",
            f["tipo"] or "", f["etapa"] or "", f["numero"] or "", f["titulo"],
            f["objeto"] or "", f["organismo"] or "", f["url"] or "",
        ])
    return buf.getvalue()


# ── Análisis con IA ──────────────────────────────────────────────────────────

SYSTEM_ANALISIS = (
    "Sos analista del Consejo Económico y Social de la Ciudad de Buenos Aires (CESBA). "
    "Escribís el análisis de un reporte sobre publicaciones del Boletín Oficial de la Ciudad.\n"
    "Reglas:\n"
    "- Español rioplatense, registro institucional, claro. 3 a 5 párrafos breves.\n"
    "- Usá SOLO las cifras y datos que te paso. No inventes montos, adjudicatarios, "
    "porcentajes ni causas que no estén en los datos. Si calculás un porcentaje, "
    "que salga de las cifras dadas.\n"
    "- Números con convención argentina (1.284; 54,9%).\n"
    "- Destacá: volumen y evolución en el tiempo, organismos que concentran la actividad, "
    "tipos de procedimiento y etapas, y temas recurrentes en los objetos de la muestra.\n"
    "- Si los datos no alcanzan para una conclusión, decilo.\n"
    "- Sin títulos, sin markdown, sin viñetas, sin preámbulos."
)


def prompt_analisis(
    filtros: dict[str, Any], total: int, ag: dict[str, Any], muestra: list[dict[str, Any]]
) -> str:
    """Prompt con los agregados del reporte y una muestra de las publicaciones recientes."""
    datos = {
        "filtros": filtros,
        "total_publicaciones": total,
        "periodo": {"desde": str(ag["desde"]), "hasta": str(ag["hasta"])},
        "organismos_distintos": ag["organismos_distintos"],
        "por_mes": ag["por_mes"],
        "top_organismos": ag["por_organismo"],
        "por_tipo": ag["por_tipo"],
        "por_etapa": ag["por_etapa"],
        "muestra_reciente": [
            {"fecha": str(f["fecha"]), "tipo": f["tipo"], "etapa": f["etapa"],
             "objeto": f["objeto"], "organismo": f["organismo"]}
            for f in muestra
        ],
    }
    return (
        "Datos del reporte (JSON). La muestra son las publicaciones más recientes, "
        "no el total:\n" + json.dumps(datos, ensure_ascii=False, default=str)
    )


# ── Programación ─────────────────────────────────────────────────────────────


def siguiente_envio(prog: dict[str, Any], despues_de: datetime) -> datetime:
    """Próximo envío (UTC) estrictamente posterior a `despues_de`, en hora ART.

    `prog`: {"frecuencia": "diaria"|"semanal"|"mensual", "hora": 0-23,
    "dia_semana": 0-6 (lunes=0), "dia_mes": 1-28}.
    """
    local = despues_de.astimezone(TZ_AR)
    hora = time(hour=int(prog.get("hora", 8)))
    frecuencia = prog.get("frecuencia", "semanal")

    def en(d: date) -> datetime:
        return datetime.combine(d, hora, tzinfo=TZ_AR)

    if frecuencia == "diaria":
        cand = en(local.date())
        if cand <= local:
            cand = en(local.date() + timedelta(days=1))
    elif frecuencia == "mensual":
        dia = max(1, min(28, int(prog.get("dia_mes", 1))))
        cand = en(local.date().replace(day=dia))
        if cand <= local:
            y, m = (local.year + 1, 1) if local.month == 12 else (local.year, local.month + 1)
            cand = en(date(y, m, min(dia, monthrange(y, m)[1])))
    else:  # semanal
        dia = int(prog.get("dia_semana", 0)) % 7
        delta = (dia - local.weekday()) % 7
        cand = en(local.date() + timedelta(days=delta))
        if cand <= local:
            cand = en(local.date() + timedelta(days=delta + 7))
    return cand.astimezone(timezone.utc)


def ventana_inicial(prog: dict[str, Any]) -> timedelta:
    """Primer envío en modo "solo lo nuevo": qué tan atrás mirar sin envío previo."""
    return {"diaria": timedelta(days=1), "mensual": timedelta(days=31)}.get(
        prog.get("frecuencia"), timedelta(days=7)
    )
