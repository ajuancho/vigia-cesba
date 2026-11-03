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

import json
from datetime import date as Date
from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select, text

from vigia_api.core.db import get_sessionmaker
from vigia_api.core.scope import jurisdiccion_scope
from vigia_api.core.security import WorkspaceContext, require_active_plan
from vigia_api.services import ai
from vigia_shared.models import Reporte
from vigia_shared.reportes import (
    CSV_MAX,
    ETAPA_EXPR,
    ORDEN_SQL,
    TIPO_EXPR,
    agregados,
    build_where,
    csv_text,
    SYSTEM_ANALISIS,
    fila_dict,
    filas_sql,
    prompt_analisis,
    siguiente_envio,
)

router = APIRouter(prefix="/reportes", tags=["reportes"])

LISTADO_MAX = 500      # filas por página en pantalla


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


class Programacion(BaseModel):
    """Envío periódico por email de un reporte guardado (hora ART)."""

    activa: bool = True
    frecuencia: Literal["diaria", "semanal", "mensual"] = "semanal"
    hora: int = Field(8, ge=0, le=23)
    dia_semana: int = Field(0, ge=0, le=6)   # lunes = 0
    dia_mes: int = Field(1, ge=1, le=28)
    # nuevo = solo lo ingestado desde el envío anterior; ventana = últimos `dias` días
    periodo: Literal["nuevo", "ventana"] = "nuevo"
    dias: int = Field(7, ge=1, le=366)
    destinatarios: list[EmailStr] = Field(min_length=1, max_length=10)
    solo_si_hay: bool = True
    incluir_ia: bool = False


class ReporteOut(BaseModel):
    id: int
    nombre: str
    config: ReporteConfig
    created_at: datetime
    updated_at: datetime
    programacion: Programacion | None = None
    proximo_envio: datetime | None = None
    ultimo_envio: datetime | None = None
    ultimo_estado: str | None = None


class AnalisisOut(BaseModel):
    texto: str


def _where(f: Filtros) -> tuple[str, dict[str, Any]]:
    """WHERE + params para los filtros del constructor (con scope de jurisdicción)."""
    return build_where(f.model_dump(), jurisdiccion=jurisdiccion_scope())


def _filas_sql(where: str, orden: str) -> str:
    return filas_sql(where, orden)


def _fila(r: Any) -> Fila:
    return Fila(**fila_dict(r))


async def _agregados(session, where: str, params: dict[str, Any]) -> tuple[int, Agregados]:
    total, ag = await agregados(session, where, params)
    return total, Agregados(**ag)


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
    contenido = csv_text([fila_dict(r) for r in rows])
    return StreamingResponse(
        iter([contenido]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="reporte.csv"'},
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

    prompt = prompt_analisis(
        config.filtros.model_dump(mode="json", exclude_defaults=True),
        total, ag.model_dump(), [fila_dict(r) for r in muestra],
    )
    texto = await ai.completar(system=SYSTEM_ANALISIS, prompt=prompt)
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
    orden = data.get("orden") if data.get("orden") in ORDEN_SQL else "fecha_desc"
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
        programacion=Programacion.model_validate(r.programacion) if r.programacion else None,
        proximo_envio=r.proximo_envio, ultimo_envio=r.ultimo_envio, ultimo_estado=r.ultimo_estado,
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


async def _reporte_propio(session, reporte_id: int, ctx: WorkspaceContext) -> Reporte:
    r = await session.get(Reporte, reporte_id)
    if r is None or r.workspace_id != ctx.workspace_id:
        raise HTTPException(404, "reporte_not_found")
    return r


@router.put("/{reporte_id}/programacion", response_model=ReporteOut)
async def programar(
    reporte_id: int,
    body: Programacion,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> ReporteOut:
    """Crea o cambia el envío periódico por email de un reporte guardado."""
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        r = await _reporte_propio(session, reporte_id, ctx)
        prog = body.model_dump(mode="json")
        r.programacion = prog
        r.proximo_envio = siguiente_envio(prog, datetime.now(timezone.utc)) if body.activa else None
        await session.commit()
        await session.refresh(r)
        return _out(r)


@router.delete("/{reporte_id}/programacion", response_model=ReporteOut)
async def desprogramar(
    reporte_id: int,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> ReporteOut:
    """Quita el envío programado (el reporte guardado queda)."""
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        r = await _reporte_propio(session, reporte_id, ctx)
        r.programacion = None
        r.proximo_envio = None
        await session.commit()
        await session.refresh(r)
        return _out(r)


@router.post("/{reporte_id}/enviar-ahora", response_model=ReporteOut)
async def enviar_ahora(
    reporte_id: int,
    ctx: Annotated[WorkspaceContext, Depends(require_active_plan)],
) -> ReporteOut:
    """Adelanta el próximo envío: el worker lo manda en su siguiente pasada (≤ 15 min)."""
    _require_real_workspace(ctx)
    Session = get_sessionmaker()
    async with Session() as session:
        r = await _reporte_propio(session, reporte_id, ctx)
        if not r.programacion:
            raise HTTPException(409, "reporte_sin_programacion")
        r.proximo_envio = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(r)
        return _out(r)
