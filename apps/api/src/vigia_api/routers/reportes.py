"""Reportes sobre el corpus normativo (JWT requerido, solo usuarios logueados).

Un reporte es una consulta con filtros (sección del boletín, tipo de
procedimiento, etapa, organismo, período, texto) que se muestra como listado
ordenable o como análisis (agregados para gráficos + texto opcional con IA).
Los reportes guardados persisten la configuración, no los resultados.

Las licitaciones del BOCBA llegan como `norma` con `bora_seccion =
'Licitaciones'`: el tipo de procedimiento está en `raw->>'tipo_nombre'`
("Licitación Obra Pública", "Contratación Menor", …) y la etapa en el título
("Licitación Pública / Adjudicación  N° 1/AGMIG/26"). Montos y adjudicatarios
no vienen en la API (solo en el PDF de cada aviso): quedan para una fase 2.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date as Date
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, text

from vigia_api.core.db import get_sessionmaker
from vigia_api.core.scope import scope_where
from vigia_api.core.security import WorkspaceContext, require_active_plan
from vigia_api.services import ai
from vigia_shared.models import Reporte

router = APIRouter(prefix="/reportes", tags=["reportes"])

# Tipo de procedimiento / tipo de norma tal como lo publica el boletín.
TIPO_EXPR = "COALESCE(raw->>'tipo_nombre', tipo)"
# Etapa de una licitación, tomada del título: "<tipo> / <etapa>  N° …".
ETAPA_EXPR = r"NULLIF(btrim(substring(titulo from ' / ([^/]+?)\s+N[°º]')), '')"

LISTADO_MAX = 500      # filas por página en pantalla
CSV_MAX = 20000        # tope de filas exportables
TOP_ORGANISMOS = 12

_ORDEN_SQL = {
    "fecha_desc": "fecha_publicacion DESC NULLS LAST, id DESC",
    "fecha_asc": "fecha_publicacion ASC NULLS LAST, id ASC",
    "organismo": "organismo ASC NULLS LAST, fecha_publicacion DESC NULLS LAST",
    "tipo": f"{TIPO_EXPR} ASC, fecha_publicacion DESC NULLS LAST",
}


def _require_real_workspace(ctx: WorkspaceContext) -> None:
    if ctx.workspace_id == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="auth_required_for_reportes")


class Filtros(BaseModel):
    secciones: list[str] = []
    tipos: list[str] = []
    etapas: list[str] = []
    organismos: list[str] = []
    desde: Date | None = None
    hasta: Date | None = None
    texto: str | None = None


class ReporteConfig(BaseModel):
    filtros: Filtros = Filtros()
    formato: Literal["listado", "analisis"] = "analisis"
    orden: Literal["fecha_desc", "fecha_asc", "organismo", "tipo"] = "fecha_desc"


class EjecutarBody(BaseModel):
    config: ReporteConfig
    limit: int = Field(100, ge=1, le=LISTADO_MAX)
    offset: int = Field(0, ge=0)


class Fila(BaseModel):
    id: int
    fecha: Date | None
    tipo: str | None
    etapa: str | None
    numero: str | None
    titulo: str
    objeto: str | None
    organismo: str | None
    url: str | None


class Conteo(BaseModel):
    valor: str
    cantidad: int


class Agregados(BaseModel):
    por_mes: list[Conteo]
    por_organismo: list[Conteo]
    por_tipo: list[Conteo]
    por_etapa: list[Conteo]
    organismos_distintos: int
    desde: Date | None
    hasta: Date | None


class Resultado(BaseModel):
    total: int
    items: list[Fila]
    agregados: Agregados


class Opciones(BaseModel):
    secciones: list[Conteo]
    tipos: list[Conteo]
    etapas: list[Conteo]
    organismos: list[Conteo]
    desde: Date | None
    hasta: Date | None


class ReporteIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    config: ReporteConfig


class ReporteOut(BaseModel):
    id: int
    nombre: str
    config: ReporteConfig
    created_at: datetime
    updated_at: datetime


class AnalisisOut(BaseModel):
    texto: str


def _where(f: Filtros) -> tuple[str, dict[str, Any]]:
    """WHERE + params para los filtros del constructor (con scope de jurisdicción)."""
    conds: list[str] = []
    params: dict[str, Any] = {}
    if f.secciones:
        conds.append("bora_seccion = ANY(:secciones)")
        params["secciones"] = f.secciones
    if f.tipos:
        conds.append(f"{TIPO_EXPR} = ANY(:tipos)")
        params["tipos"] = f.tipos
    if f.etapas:
        conds.append(f"{ETAPA_EXPR} = ANY(:etapas)")
        params["etapas"] = f.etapas
    if f.organismos:
        conds.append("organismo = ANY(:organismos)")
        params["organismos"] = f.organismos
    if f.desde:
        conds.append("fecha_publicacion >= :desde")
        params["desde"] = f.desde
    if f.hasta:
        conds.append("fecha_publicacion <= :hasta")
        params["hasta"] = f.hasta
    if f.texto and f.texto.strip():
        conds.append("search_vector @@ websearch_to_tsquery('spanish', :texto)")
        params["texto"] = f.texto.strip()
    conds, params = scope_where(conds, params)
    return ("WHERE " + " AND ".join(conds)) if conds else "", params


def _filas_sql(where: str, orden: str) -> str:
    return f"""
        SELECT id, fecha_publicacion, {TIPO_EXPR} AS tipo, {ETAPA_EXPR} AS etapa,
               numero, titulo, resumen, organismo, url
        FROM norma {where}
        ORDER BY {_ORDEN_SQL[orden]}
        LIMIT :_limit OFFSET :_offset
    """


def _fila(r: Any) -> Fila:
    return Fila(
        id=r[0], fecha=r[1], tipo=r[2], etapa=r[3], numero=r[4],
        titulo=r[5], objeto=r[6], organismo=r[7], url=r[8],
    )


async def _agregados(session, where: str, params: dict[str, Any]) -> tuple[int, Agregados]:
    async def conteo(expr: str, limit: int | None = None) -> list[Conteo]:
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
        return [Conteo(valor=str(r[0]), cantidad=int(r[1])) for r in rows]

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
    return int(resumen[0] or 0), Agregados(
        por_mes=[Conteo(valor=r[0], cantidad=int(r[1])) for r in por_mes],
        por_organismo=await conteo("organismo", TOP_ORGANISMOS),
        por_tipo=await conteo(TIPO_EXPR, 20),
        por_etapa=await conteo(ETAPA_EXPR, 10),
        organismos_distintos=int(resumen[1] or 0),
        desde=resumen[2],
        hasta=resumen[3],
    )


@router.get("/opciones", response_model=Opciones)
async def opciones(
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
    secciones: Annotated[list[str] | None, Query()] = None,
) -> Opciones:
    """Valores disponibles para los filtros. `secciones` acota tipos/etapas/organismos."""
    _require_real_workspace(ctx)
    where_all, params_all = _where(Filtros())
    where_sec, params_sec = _where(Filtros(secciones=secciones or []))
    Session = get_sessionmaker()
    async with Session() as session:
        async def conteo(expr: str, where: str, params: dict, limit: int) -> list[Conteo]:
            rows = (
                await session.execute(
                    text(
                        f"SELECT v, c FROM (SELECT {expr} AS v, COUNT(*) c FROM norma {where} "
                        f"GROUP BY 1) t WHERE v IS NOT NULL ORDER BY c DESC LIMIT {limit}"
                    ),
                    params,
                )
            ).all()
            return [Conteo(valor=str(r[0]), cantidad=int(r[1])) for r in rows]

        rango = (
            await session.execute(
                text(f"SELECT MIN(fecha_publicacion), MAX(fecha_publicacion) FROM norma {where_all}"),
                params_all,
            )
        ).one()
        return Opciones(
            secciones=await conteo("bora_seccion", where_all, params_all, 50),
            tipos=await conteo(TIPO_EXPR, where_sec, params_sec, 60),
            etapas=await conteo(ETAPA_EXPR, where_sec, params_sec, 20),
            organismos=await conteo("organismo", where_sec, params_sec, 300),
            desde=rango[0],
            hasta=rango[1],
        )


@router.post("/ejecutar", response_model=Resultado)
async def ejecutar(
    body: EjecutarBody,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> Resultado:
    _require_real_workspace(ctx)
    where, params = _where(body.config.filtros)
    Session = get_sessionmaker()
    async with Session() as session:
        total, agregados = await _agregados(session, where, params)
        rows = (
            await session.execute(
                text(_filas_sql(where, body.config.orden)),
                {**params, "_limit": body.limit, "_offset": body.offset},
            )
        ).all()
    return Resultado(total=total, items=[_fila(r) for r in rows], agregados=agregados)


@router.post("/csv")
async def exportar_csv(
    config: ReporteConfig,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> StreamingResponse:
    """Todas las filas del reporte (hasta CSV_MAX) en CSV para Excel (`;`, UTF-8 con BOM)."""
    _require_real_workspace(ctx)
    where, params = _where(config.filtros)
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.execute(
                text(_filas_sql(where, config.orden)),
                {**params, "_limit": CSV_MAX, "_offset": 0},
            )
        ).all()
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Fecha", "Tipo", "Etapa", "Número", "Título", "Objeto", "Organismo", "URL"])
    for r in rows:
        f = _fila(r)
        w.writerow([
            f.fecha.strftime("%d/%m/%Y") if f.fecha else "",
            f.tipo or "", f.etapa or "", f.numero or "", f.titulo,
            f.objeto or "", f.organismo or "", f.url or "",
        ])
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="reporte.csv"'},
    )


_SYSTEM_ANALISIS = (
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


@router.post("/analisis", response_model=AnalisisOut)
async def analisis(
    config: ReporteConfig,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> AnalisisOut:
    """Texto de análisis con IA sobre los agregados del reporte y una muestra de objetos."""
    _require_real_workspace(ctx)
    if not ai.enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ia_no_configurada")
    where, params = _where(config.filtros)
    Session = get_sessionmaker()
    async with Session() as session:
        total, ag = await _agregados(session, where, params)
        muestra = (
            await session.execute(
                text(_filas_sql(where, "fecha_desc")),
                {**params, "_limit": 80, "_offset": 0},
            )
        ).all()
    if total == 0:
        return AnalisisOut(texto="El reporte no tiene resultados para analizar con los filtros elegidos.")

    datos = {
        "filtros": config.filtros.model_dump(mode="json", exclude_defaults=True),
        "total_publicaciones": total,
        "periodo": {"desde": str(ag.desde), "hasta": str(ag.hasta)},
        "organismos_distintos": ag.organismos_distintos,
        "por_mes": [c.model_dump() for c in ag.por_mes],
        "top_organismos": [c.model_dump() for c in ag.por_organismo],
        "por_tipo": [c.model_dump() for c in ag.por_tipo],
        "por_etapa": [c.model_dump() for c in ag.por_etapa],
        "muestra_reciente": [
            {"fecha": str(r[1]), "tipo": r[2], "etapa": r[3], "objeto": r[6], "organismo": r[7]}
            for r in muestra
        ],
    }
    prompt = (
        "Datos del reporte (JSON). La muestra son las publicaciones más recientes, "
        "no el total:\n" + json.dumps(datos, ensure_ascii=False, default=str)
    )
    texto = await ai.completar(system=_SYSTEM_ANALISIS, prompt=prompt)
    if not texto:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ia_fallo")
    return AnalisisOut(texto=texto)


# ── Pedido en lenguaje natural → configuración del constructor ──────────────


class PedidoIn(BaseModel):
    pedido: str = Field(min_length=3, max_length=1000)


class InterpretacionOut(BaseModel):
    config: ReporteConfig
    explicacion: str
    descartados: list[str] = []  # valores que propuso la IA y no existen en la base


_SYSTEM_INTERPRETAR = (
    "Convertís pedidos de reportes sobre el Boletín Oficial de la Ciudad de Buenos Aires "
    "en filtros para un constructor de reportes. Respondés SOLO un objeto JSON, sin texto "
    "alrededor, con esta forma:\n"
    '{"filtros": {"secciones": [], "tipos": [], "etapas": [], "organismos": [], '
    '"desde": null, "hasta": null, "texto": null}, "formato": "analisis", '
    '"orden": "fecha_desc", "explicacion": ""}\n'
    "Reglas:\n"
    "- secciones, tipos, etapas y organismos: usá SOLO valores copiados textualmente de las "
    "listas disponibles que te paso. Lista vacía = sin restricción.\n"
    "- Licitaciones, compras y contrataciones están en la sección 'Licitaciones'; su tipo de "
    "procedimiento va en 'tipos' (p.ej. 'Licitación Obra Pública') y la etapa (llamado, "
    "preadjudicación, adjudicación…) en 'etapas'.\n"
    "- desde/hasta: fechas ISO (AAAA-MM-DD) calculadas a partir de la fecha de hoy que te paso. "
    "'el último año' = hoy menos 365 días. Sin período en el pedido = null.\n"
    "- texto: solo palabras del tema que no cubran los otros filtros (p.ej. 'hospital', "
    "'residuos'). Sintaxis: palabras sueltas (todas deben aparecer), \"frase exacta\", "
    "'or' entre alternativas, '-palabra' para excluir. Sin tema = null.\n"
    "- formato: 'analisis' si pide análisis, cantidades, promedios, rankings o comparaciones; "
    "'listado' si pide listar, compilar o enumerar.\n"
    "- orden: fecha_desc | fecha_asc | organismo | tipo.\n"
    "- explicacion: una frase en español rioplatense que diga qué vas a mostrar. Si el pedido "
    "incluye algo que los datos no tienen (montos, adjudicatarios, presupuestos), aclaralo ahí."
)


def _parse_json(texto: str) -> dict[str, Any] | None:
    """Primer objeto JSON del texto (tolera ```json …``` u otro envoltorio)."""
    ini, fin = texto.find("{"), texto.rfind("}")
    if ini < 0 or fin <= ini:
        return None
    try:
        data = json.loads(texto[ini : fin + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _canon(valores: Any, disponibles: list[str], descartados: list[str]) -> list[str]:
    """Mapea los valores propuestos a los disponibles (sin distinguir mayúsculas)."""
    por_clave = {d.casefold(): d for d in disponibles}
    out: list[str] = []
    for v in valores if isinstance(valores, list) else []:
        c = por_clave.get(str(v).strip().casefold())
        if c is None:
            descartados.append(str(v))
        elif c not in out:
            out.append(c)
    return out


def _fecha(v: Any) -> Date | None:
    try:
        return Date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


@router.post("/interpretar", response_model=InterpretacionOut)
async def interpretar(
    body: PedidoIn,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> InterpretacionOut:
    """Traduce un pedido en lenguaje natural a la configuración del constructor."""
    _require_real_workspace(ctx)
    if not ai.enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ia_no_configurada")

    where_all, params_all = _where(Filtros())
    Session = get_sessionmaker()
    async with Session() as session:
        async def valores(expr: str, limit: int) -> list[str]:
            rows = (
                await session.execute(
                    text(
                        f"SELECT v FROM (SELECT {expr} AS v, COUNT(*) c FROM norma {where_all} "
                        f"GROUP BY 1) t WHERE v IS NOT NULL ORDER BY c DESC LIMIT {limit}"
                    ),
                    params_all,
                )
            ).all()
            return [str(r[0]) for r in rows]

        secciones = await valores("bora_seccion", 50)
        tipos = await valores(TIPO_EXPR, 80)
        etapas = await valores(ETAPA_EXPR, 20)
        organismos = await valores("organismo", 300)

    contexto = {
        "hoy": Date.today().isoformat(),
        "secciones": secciones,
        "tipos": tipos,
        "etapas": etapas,
        "organismos": organismos,
    }
    prompt = (
        "Valores disponibles (JSON):\n" + json.dumps(contexto, ensure_ascii=False)
        + f'\n\nPedido del usuario:\n"""\n{body.pedido.strip()}\n"""'
    )
    respuesta = await ai.completar(system=_SYSTEM_INTERPRETAR, prompt=prompt, max_tokens=800)
    data = _parse_json(respuesta or "")
    if data is None:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ia_fallo")

    f = data.get("filtros") if isinstance(data.get("filtros"), dict) else {}
    descartados: list[str] = []
    texto = f.get("texto")
    filtros = Filtros(
        secciones=_canon(f.get("secciones"), secciones, descartados),
        tipos=_canon(f.get("tipos"), tipos, descartados),
        etapas=_canon(f.get("etapas"), etapas, descartados),
        organismos=_canon(f.get("organismos"), organismos, descartados),
        desde=_fecha(f.get("desde")),
        hasta=_fecha(f.get("hasta")),
        texto=str(texto).strip()[:200] if texto else None,
    )
    formato = data.get("formato") if data.get("formato") in ("listado", "analisis") else "analisis"
    orden = data.get("orden") if data.get("orden") in _ORDEN_SQL else "fecha_desc"
    return InterpretacionOut(
        config=ReporteConfig(filtros=filtros, formato=formato, orden=orden),
        explicacion=str(data.get("explicacion") or "").strip()[:500],
        descartados=descartados,
    )


# ── Reportes guardados ──────────────────────────────────────────────────────


def _out(r: Reporte) -> ReporteOut:
    return ReporteOut(
        id=r.id, nombre=r.nombre, config=ReporteConfig.model_validate(r.config),
        created_at=r.created_at, updated_at=r.updated_at,
    )


@router.get("", response_model=list[ReporteOut])
async def listar(ctx: Annotated[WorkspaceContext, Depends(require_active_plan)]) -> list[ReporteOut]:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        rows = (
            await session.scalars(
                select(Reporte)
                .where(Reporte.workspace_id == ctx.workspace_id)
                .order_by(Reporte.updated_at.desc())
            )
        ).all()
    return [_out(r) for r in rows]


@router.post("", response_model=ReporteOut, status_code=status.HTTP_201_CREATED)
async def crear(
    body: ReporteIn,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> ReporteOut:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        r = Reporte(
            workspace_id=ctx.workspace_id, user_id=ctx.user_id,
            nombre=body.nombre.strip(), config=body.config.model_dump(mode="json"),
        )
        session.add(r)
        await session.commit()
        await session.refresh(r)
        return _out(r)


@router.put("/{reporte_id}", response_model=ReporteOut)
async def actualizar(
    reporte_id: int,
    body: ReporteIn,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> ReporteOut:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        r = await session.get(Reporte, reporte_id)
        if r is None or r.workspace_id != ctx.workspace_id:
            raise HTTPException(404, "reporte_not_found")
        r.nombre = body.nombre.strip()
        r.config = body.config.model_dump(mode="json")
        await session.commit()
        await session.refresh(r)
        return _out(r)


@router.delete("/{reporte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def borrar(
    reporte_id: int,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> None:
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        res = await session.execute(
            delete(Reporte).where(Reporte.id == reporte_id, Reporte.workspace_id == ctx.workspace_id)
        )
        await session.commit()
    if res.rowcount == 0:
        raise HTTPException(404, "reporte_not_found")
