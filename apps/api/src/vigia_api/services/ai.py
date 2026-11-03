"""Cliente LLM para la API (análisis escrito de reportes).

Misma configuración por entorno que `vigia_workers.ai_resumen`:
``VIGIA_AI_PROVIDER`` = off | bedrock | anthropic (default off → no-op),
``AWS_REGION`` / ``AWS_BEDROCK_MODEL_HAIKU`` para Bedrock y
``VIGIA_AI_MODEL`` para la API directa de Anthropic.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

_PROVIDER = os.environ.get("VIGIA_AI_PROVIDER", "off").strip().lower()
_AWS_REGION = os.environ.get("AWS_REGION", "us-east-1").strip() or "us-east-1"
_MODEL_BEDROCK = (
    os.environ.get("AWS_BEDROCK_MODEL_HAIKU", "us.anthropic.claude-haiku-4-5-20251001-v1:0").strip()
    or "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)
_MODEL_ANTHROPIC = os.environ.get("VIGIA_AI_MODEL", "claude-haiku-4-5").strip() or "claude-haiku-4-5"


def enabled() -> bool:
    """True si hay un proveedor LLM configurado."""
    return _PROVIDER in ("bedrock", "anthropic")


def _make_client() -> tuple[object, str]:
    if _PROVIDER == "anthropic":
        from anthropic import AsyncAnthropic

        return AsyncAnthropic(timeout=90.0), _MODEL_ANTHROPIC
    from anthropic import AsyncAnthropicBedrock

    return AsyncAnthropicBedrock(aws_region=_AWS_REGION, timeout=90.0), _MODEL_BEDROCK


async def completar(*, system: str, prompt: str, max_tokens: int = 1200) -> str | None:
    """Una llamada de texto. Devuelve None si está apagado o si el proveedor falla."""
    if not enabled():
        return None
    client, model = _make_client()
    try:
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:  # permisos, throttling, refusal, etc. -> degradar
        log.warning("análisis IA falló: %s", exc)
        return None
    out = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    return out or None
