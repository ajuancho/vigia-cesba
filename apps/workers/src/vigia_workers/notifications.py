"""Envío de email via Resend (HTTP API). No-op limpio si falta RESEND_API_KEY."""
from __future__ import annotations

import os

import httpx

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ALERTS_FROM_EMAIL = os.environ.get("ALERTS_FROM_EMAIL", "alertas@vigia.legal")
RESEND_URL = "https://api.resend.com/emails"


def send_email(*, to: str, subject: str, html: str) -> dict:
    """Envía un email. Si no hay API key, loguea y devuelve {'skipped': True}."""
    if not RESEND_API_KEY:
        print(f"[notifications] (sin RESEND_API_KEY) email a {to}: {subject}")
        return {"skipped": True, "to": to}
    try:
        resp = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": ALERTS_FROM_EMAIL, "to": [to], "subject": subject, "html": html},
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"sent": True, "to": to, "id": resp.json().get("id")}
    except Exception as exc:  # pragma: no cover
        print(f"[notifications] error enviando a {to}: {exc!r}")
        return {"error": str(exc), "to": to}


def render_digest(workspace_name: str, items: list[dict]) -> str:
    """HTML simple de digest de alertas."""
    rows = "".join(
        f'<li style="margin-bottom:10px">'
        f'<strong>{i["keyword"]}</strong> — {i["tipo"]} {i.get("numero") or ""}: '
        f'{i["titulo"]}</li>'
        for i in items
    )
    return (
        f'<div style="font-family:Inter,sans-serif;color:#111827">'
        f'<h2 style="color:#1a2d4d">Vigía — nuevas normas para {workspace_name}</h2>'
        f'<p>Se detectaron {len(items)} coincidencias con tus alertas:</p>'
        f'<ul style="padding-left:18px">{rows}</ul>'
        f'<p style="color:#9ca3af;font-size:12px">Inteligencia legislativa · Colossus Lab</p>'
        f'</div>'
    )
