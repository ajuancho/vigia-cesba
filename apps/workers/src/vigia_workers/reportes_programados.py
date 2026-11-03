"""Envío periódico por email de reportes guardados.

`enviar_reportes_programados` corre cada 15 min (beat). Toma los reportes con
`proximo_envio <= now()`, reserva el turno moviendo `proximo_envio` al próximo
horario ANTES de enviar (dos corridas solapadas no duplican el email), arma el
reporte con las consultas compartidas (`vigia_shared.reportes`) y lo manda a
cada destinatario con resumen, primeras filas, CSV adjunto y, opcionalmente,
análisis con IA.

Período de cada envío (`programacion.periodo`):
- ``nuevo``: solo normas ingestadas desde el envío anterior (el primer envío
  mira una frecuencia hacia atrás). Ignora el desde/hasta guardado.
- ``ventana``: publicadas en los últimos ``dias`` días.
"""
from __future__ import annotations

import html as _html
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text

from vigia_shared.db import session_scope
from vigia_shared.reportes import (
    CSV_MAX,
    SYSTEM_ANALISIS,
    TZ_AR,
    agregados,
    build_where,
    csv_text,
    fila_dict,
    filas_sql,
    prompt_analisis,
    siguiente_envio,
    ventana_inicial,
)
from vigia_workers import ai_resumen
from vigia_workers.celery_app import celery_app
from vigia_workers.notifications import WEB_BASE_URL, send_email
from vigia_workers.persistence import run_async

log = logging.getLogger(__name__)

MAX_POR_CORRIDA = 20
FILAS_EN_EMAIL = 25
_JURISDICCION = os.environ.get("VIGIA_JURISDICCION_SCOPE", "").strip() or None


def _esc(v: Any) -> str:
    return _html.escape(str(v)) if v is not None else ""


def _fmt_fecha(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "—"


def _fmt_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _describir_periodo(prog: dict[str, Any], desde_ingesta: datetime | None) -> str:
    if prog.get("periodo") == "ventana":
        return f"publicado en los últimos {int(prog.get('dias', 7))} días"
    if desde_ingesta:
        return "novedades desde el " + desde_ingesta.astimezone(TZ_AR).strftime("%d/%m/%Y %H:%M")
    return "novedades"


def render_reporte(
    *, reporte_id: int, nombre: str, periodo: str, total: int, ag: dict[str, Any],
    filas: list[dict[str, Any]], analisis: str | None,
) -> str:
    """HTML del email con la identidad CESBA (claro, petróleo + cian)."""
    petroleo, cian, gris, borde = "#18596C", "#18A6C2", "#5B6267", "#E4EBED"

    def top(titulo: str, datos: list[dict[str, Any]]) -> str:
        if not datos:
            return ""
        items = "".join(
            f'<tr><td style="padding:4px 0;font-size:13px;color:#2A3438">{_esc(d["valor"])}</td>'
            f'<td style="padding:4px 0;font-size:13px;color:{petroleo};font-weight:700;text-align:right">'
            f'{_fmt_num(d["cantidad"])}</td></tr>'
            for d in datos[:5]
        )
        return (
            f'<td style="vertical-align:top;padding:0 12px 0 0;width:50%">'
            f'<p style="margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:.08em;color:{petroleo}">{titulo}</p>'
            f'<table style="width:100%;border-collapse:collapse">{items}</table></td>'
        )

    filas_html = "".join(
        f'<tr><td style="padding:8px 8px 8px 0;border-top:1px solid {borde};font-size:12px;color:{gris};white-space:nowrap;vertical-align:top">{_fmt_fecha(f["fecha"])}</td>'
        f'<td style="padding:8px 8px 8px 0;border-top:1px solid {borde};font-size:12px;color:{gris};vertical-align:top">{_esc(f["tipo"])}'
        f'{"<br>" + _esc(f["etapa"]) if f["etapa"] else ""}</td>'
        f'<td style="padding:8px 0;border-top:1px solid {borde};font-size:13px;vertical-align:top">'
        + (f'<a href="{_esc(f["url"])}" style="color:{petroleo};font-weight:600;text-decoration:none">{_esc(f["objeto"] or f["titulo"])}</a>'
           if f["url"] else f'<span style="color:{petroleo};font-weight:600">{_esc(f["objeto"] or f["titulo"])}</span>')
        + f'<br><span style="font-size:12px;color:{gris}">{_esc(f["organismo"])}</span></td></tr>'
        for f in filas
    )
    resto = (
        f'<p style="margin:10px 0 0;font-size:12px;color:{gris}">Y {_fmt_num(total - len(filas))} más en el CSV adjunto.</p>'
        if total > len(filas) else ""
    )
    analisis_html = (
        f'<div style="margin:22px 0 0;padding:16px;background:#F4F7F8;border-radius:8px">'
        f'<p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:.08em;color:{petroleo}">ANÁLISIS</p>'
        + "".join(f'<p style="margin:0 0 8px;font-size:13px;line-height:1.55;color:#2A3438">{_esc(p)}</p>'
                  for p in analisis.split("\n") if p.strip())
        + f'<p style="margin:6px 0 0;font-size:11px;color:{gris}">Texto generado con IA a partir de las cifras del reporte.</p></div>'
        if analisis else ""
    )
    return (
        f'<div style="font-family:Montserrat,Arial,sans-serif;background:#FFFFFF;max-width:640px;border:1px solid {borde};border-radius:8px;overflow:hidden">'
        f'<div style="background:linear-gradient(180deg,#1B9FC7 0%,#153B70 100%);background-color:#153B70;padding:22px 24px;color:#FFFFFF">'
        f'<p style="margin:0 0 6px;font-size:11px;letter-spacing:.14em">MONITOR BOCBA · REPORTE PROGRAMADO</p>'
        f'<p style="margin:0;font-size:20px;font-weight:700;letter-spacing:.04em;text-transform:uppercase">{_esc(nombre)}</p>'
        f'<p style="margin:4px 0 0;font-size:13px;color:rgba(255,255,255,.86)">{_esc(periodo)}</p></div>'
        f'<div style="padding:22px 24px;border-top:3px solid {cian}">'
        f'<p style="margin:0;font-size:34px;font-weight:700;color:{petroleo}">{_fmt_num(total)}</p>'
        f'<p style="margin:2px 0 18px;font-size:11px;font-weight:600;letter-spacing:.14em;color:{gris}">PUBLICACIONES · {ag["organismos_distintos"]} ORGANISMOS</p>'
        f'<table style="width:100%;border-collapse:collapse;margin:0 0 18px"><tr>'
        f'{top("ORGANISMOS", ag["por_organismo"])}{top("TIPOS", ag["por_tipo"])}</tr></table>'
        f'<table style="width:100%;border-collapse:collapse">{filas_html}</table>{resto}'
        f'{analisis_html}'
        f'<p style="margin:22px 0 0"><a href="{WEB_BASE_URL}/reportes?r={int(reporte_id)}" '
        f'style="display:inline-block;background:{cian};color:#FFFFFF;font-weight:700;font-size:13px;letter-spacing:.06em;'
        f'padding:11px 20px;border-radius:4px;text-decoration:none">ABRIR EN EL MONITOR</a></p></div>'
        f'<div style="padding:12px 24px;border-top:1px solid {borde};font-size:11px;color:{gris}">'
        f'www.cesba.gob.ar · Consejo Económico y Social de la Ciudad de Buenos Aires<br>'
        f'Recibís este email porque alguien de tu equipo programó este reporte en el monitor.</div></div>'
    )


async def _analisis_ia(filtros: dict[str, Any], total: int, ag: dict[str, Any], muestra: list[dict]) -> str | None:
    if not ai_resumen.enabled() or total == 0:
        return None
    client, model = ai_resumen._make_client()
    try:
        resp = await client.messages.create(
            model=model, max_tokens=1200, system=SYSTEM_ANALISIS,
            messages=[{"role": "user", "content": prompt_analisis(filtros, total, ag, muestra)}],
        )
    except Exception as exc:  # degradar: el reporte sale igual, sin análisis
        log.warning("análisis IA del reporte programado falló: %s", exc)
        return None
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip() or None


async def _procesar(r: Any, ahora: datetime) -> str:
    """Arma y envía un reporte. Devuelve el estado a registrar."""
    prog: dict[str, Any] = r.programacion
    filtros = dict((r.config or {}).get("filtros") or {})
    orden = (r.config or {}).get("orden") or "fecha_desc"
    desde_ingesta: datetime | None = None
    if prog.get("periodo") == "ventana":
        filtros["desde"] = (ahora.astimezone(TZ_AR).date() - timedelta(days=int(prog.get("dias", 7)))).isoformat()
        filtros["hasta"] = None
    else:
        filtros["desde"] = filtros["hasta"] = None
        desde_ingesta = r.ultimo_envio or (ahora - ventana_inicial(prog))

    where, params = build_where(filtros, jurisdiccion=_JURISDICCION, ingestado_desde=desde_ingesta)
    async with session_scope() as session:
        total, ag = await agregados(session, where, params)
        rows = (
            await session.execute(text(filas_sql(where, orden)), {**params, "_limit": CSV_MAX, "_offset": 0})
        ).all()
    filas = [fila_dict(x) for x in rows]

    if total == 0 and prog.get("solo_si_hay", True):
        return "sin novedades: no se envió"

    analisis = await _analisis_ia(filtros, total, ag, filas[:80]) if prog.get("incluir_ia") else None
    periodo = _describir_periodo(prog, desde_ingesta)
    html = render_reporte(
        reporte_id=r.id, nombre=r.nombre, periodo=periodo, total=total, ag=ag,
        filas=filas[:FILAS_EN_EMAIL], analisis=analisis,
    )
    fecha = ahora.astimezone(TZ_AR).strftime("%Y-%m-%d")
    adjuntos = [(f"reporte-{r.id}-{fecha}.csv", csv_text(filas).encode("utf-8"), "text/csv")] if filas else []
    subject = f"Reporte «{r.nombre}» — {_fmt_num(total)} publicaciones"

    ok = 0
    for dest in prog.get("destinatarios") or []:
        res = send_email(to=dest, subject=subject, html=html, adjuntos=adjuntos)
        ok += 1 if res.get("sent") else 0
    n = len(prog.get("destinatarios") or [])
    if ok == n:
        return f"enviado a {n} destinatario{'s' if n != 1 else ''} ({total} publicaciones)"
    if ok == 0:
        return "error: no se pudo enviar (revisá la configuración de email del servidor)"
    return f"enviado a {ok} de {n} destinatarios"


async def _enviar_programados(ahora: datetime | None = None) -> dict[str, Any]:
    ahora = ahora or datetime.now(timezone.utc)
    # 1) Reservar los turnos vencidos (y correr proximo_envio) en una transacción.
    async with session_scope() as session:
        vencidos = (
            await session.execute(
                text(
                    """
                    SELECT id, nombre, config, programacion, ultimo_envio
                    FROM reporte
                    WHERE proximo_envio IS NOT NULL AND proximo_envio <= :ahora
                      AND programacion IS NOT NULL
                    ORDER BY proximo_envio
                    LIMIT :lim
                    FOR UPDATE SKIP LOCKED
                    """
                ),
                {"ahora": ahora, "lim": MAX_POR_CORRIDA},
            )
        ).all()
        for r in vencidos:
            await session.execute(
                text("UPDATE reporte SET proximo_envio = :prox WHERE id = :id"),
                {"prox": siguiente_envio(r.programacion, ahora), "id": r.id},
            )

    # 2) Armar y enviar cada uno; registrar el resultado.
    resultados = {}
    for r in vencidos:
        try:
            estado = await _procesar(r, ahora)
        except Exception as exc:
            log.exception("reporte programado %s falló", r.id)
            estado = f"error: {exc.__class__.__name__}"
        async with session_scope() as session:
            await session.execute(
                text("UPDATE reporte SET ultimo_envio = :ahora, ultimo_estado = :estado WHERE id = :id"),
                {"ahora": ahora, "estado": estado[:255], "id": r.id},
            )
        resultados[r.id] = estado
    return {"procesados": len(vencidos), "resultados": resultados}


@celery_app.task(name="vigia_workers.reportes_programados.enviar_reportes_programados")
def enviar_reportes_programados() -> dict[str, Any]:
    return run_async(_enviar_programados())
