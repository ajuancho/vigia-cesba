"""Resúmenes en lenguaje claro generados por LLM (campo `resumen_ia`).

Capa opcional sobre la ingesta. Cuando hay texto fuente real (el cuerpo de un
aviso del Boletín Oficial, el `texto_resumido` de InfoLEG) produce 2-3 frases
llanas de QUÉ hace la norma — el valor que el sumario del BO no da cuando trae
solo el código del documento (p.ej. ``RESOL-2026-276-APN-INASE#MEC``).

Stack: **AWS Bedrock** vía `anthropic[bedrock]` (`AsyncAnthropicBedrock`),
calcando la convención de la familia OpenArg (ver `../investarg`: model ids
estilo Bedrock, `AWS_REGION`, credenciales por IAM). La API directa de Anthropic
queda como fallback explícito.

Diseño:
- **Opt-in por entorno** (`VIGIA_AI_PROVIDER`): default ``off`` -> no-op total
  (la ingesta sigue igual, `resumen_ia` queda NULL). ``bedrock`` o ``anthropic``
  lo encienden. Cero costos sorpresa al desplegar.
- **Resiliente**: cualquier error (permisos, throttling, refusal) degrada a
  ``None`` para esa fila — nunca rompe la corrida de ingesta.
- **Barato**: Haiku, recorte del texto fuente y concurrencia acotada.
"""
from __future__ import annotations

import asyncio
import logging
import os

log = logging.getLogger(__name__)

# off | bedrock | anthropic. Default off para no llamar a ningún LLM sin pedirlo.
_PROVIDER = os.environ.get("VIGIA_AI_PROVIDER", "off").strip().lower()
_AWS_REGION = os.environ.get("AWS_REGION", "us-east-1").strip() or "us-east-1"
# Perfil de inferencia de Bedrock. Claude 4.x NO admite on-demand sobre el id
# pelado (`anthropic.claude-…`) — hay que invocar el inference profile regional.
# Verificado en la cuenta del lab (us-east-1): el `us.` responde, el pelado
# tira ValidationException. Cambiable por env (p.ej. `global.anthropic.…`).
_MODEL_BEDROCK = (
    os.environ.get("AWS_BEDROCK_MODEL_HAIKU", "us.anthropic.claude-haiku-4-5-20251001-v1:0").strip()
    or "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)
# Fallback API directa de Anthropic: model id first-party.
_MODEL_ANTHROPIC = os.environ.get("VIGIA_AI_MODEL", "claude-haiku-4-5").strip() or "claude-haiku-4-5"

# Mínimo de caracteres de texto fuente para que valga la pena resumir.
_MIN_TEXTO = 200
# Cuánto texto fuente mandamos al modelo (recorte por costo/latencia; el VISTO +
# CONSIDERANDO + parte resolutiva inicial entran de sobra en este margen).
_MAX_TEXTO = 6000
# Llamadas concurrentes al API por corrida.
_MAX_CONCURRENCY = 5
# Centinela que el modelo devuelve cuando el texto no alcanza para algo útil.
_SENTINEL = "SIN_RESUMEN"

_SYSTEM = (
    "Sos un analista legislativo argentino. Resumís normas del Boletín Oficial "
    "para profesionales (abogados, despachantes de aduana, compliance) que "
    "necesitan saber QUÉ resuelve la norma sin leer el texto completo.\n"
    "Reglas:\n"
    "- 1 a 3 frases, en español rioplatense neutro y claro.\n"
    "- Decí qué se crea/modifica/deroga/autoriza/sanciona y a quién afecta. "
    "Incluí datos concretos (montos, plazos, organismos, sujetos, expedientes) "
    "si aparecen en el texto.\n"
    "- No inventes ni infieras nada que no esté en el texto. No agregues "
    "interpretación legal ni consecuencias no escritas.\n"
    f"- Si el texto no alcanza para un resumen útil, respondé exactamente: {_SENTINEL}\n"
    "- Sin preámbulos ('Esta resolución…', 'El presente…'), sin markdown, sin "
    "comillas. Devolvé solo el resumen."
)


def enabled() -> bool:
    """True si hay un proveedor LLM configurado (si no, todo es no-op)."""
    return _PROVIDER in ("bedrock", "anthropic")


def _make_client() -> tuple[object, str]:
    """Crea el cliente async según el proveedor. Devuelve (client, model_id).

    Bedrock resuelve credenciales AWS por la cadena estándar de boto3
    (env vars, perfil, o el rol de instancia del EC2)."""
    if _PROVIDER == "anthropic":
        from anthropic import AsyncAnthropic

        return AsyncAnthropic(timeout=60.0), _MODEL_ANTHROPIC
    from anthropic import AsyncAnthropicBedrock

    return AsyncAnthropicBedrock(aws_region=_AWS_REGION, timeout=60.0), _MODEL_BEDROCK


def _build_prompt(*, titulo: str | None, organismo: str | None, texto: str) -> str:
    encabezado = "\n".join(
        p
        for p in (
            f"Identificador/tipo: {titulo}" if titulo else None,
            f"Organismo emisor: {organismo}" if organismo else None,
        )
        if p
    )
    cuerpo = f'Texto del Boletín Oficial:\n"""\n{texto[:_MAX_TEXTO].strip()}\n"""'
    return f"{encabezado}\n\n{cuerpo}" if encabezado else cuerpo


async def _resumir_uno(client, *, model, titulo, organismo, texto) -> str | None:
    try:
        resp = await client.messages.create(
            model=model,
            max_tokens=300,
            system=_SYSTEM,
            messages=[
                {"role": "user", "content": _build_prompt(
                    titulo=titulo, organismo=organismo, texto=texto)}
            ],
        )
    except Exception as exc:  # permisos, throttling, refusal, etc. -> degradar
        log.warning("resumen_ia falló: %s", exc)
        return None
    out = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    if not out or _SENTINEL in out:
        return None
    return out


async def aplicar_resumen_ia(rows: list[dict], textos: dict[str, str]) -> int:
    """Rellena ``row['resumen_ia']`` in-place para las filas con texto suficiente.

    `rows`: filas con shape de `norma` (cada una debe traer la key `resumen_ia`).
    `textos`: ``external_id -> texto completo`` del detalle (BORA) o fuente.
    Devuelve cuántos resúmenes se generaron. No-op (devuelve 0) si está apagado.
    """
    if not enabled():
        return 0
    pendientes = [
        r
        for r in rows
        if (t := textos.get(r.get("external_id"))) and len(t) >= _MIN_TEXTO
    ]
    if not pendientes:
        return 0

    client, model = _make_client()
    sem = asyncio.Semaphore(_MAX_CONCURRENCY)
    generados = 0

    async with client:
        async def _one(row: dict) -> None:
            nonlocal generados
            async with sem:
                resumen = await _resumir_uno(
                    client,
                    model=model,
                    titulo=row.get("titulo"),
                    organismo=row.get("organismo"),
                    texto=textos[row["external_id"]],
                )
            if resumen:
                row["resumen_ia"] = resumen
                generados += 1

        await asyncio.gather(*(_one(r) for r in pendientes), return_exceptions=True)

    log.info("resumen_ia: %d/%d generados (%s, %s)", generados, len(pendientes), _PROVIDER, model)
    return generados
