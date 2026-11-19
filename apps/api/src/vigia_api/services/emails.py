"""Emails transaccionales de la API (invitaciones) vía Resend.

Mismo patrón que vigia_workers.notifications: no-op limpio sin RESEND_API_KEY
(la key vive solo en el entorno, nunca en el repo). El envío es best-effort:
una invitación se crea igual aunque el email falle — el link compartible por
WhatsApp/copia es el camino principal.
"""
from __future__ import annotations

import os

import httpx

from vigia_shared.email_marca import invitacion

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ALERTS_FROM_EMAIL = os.environ.get("ALERTS_FROM_EMAIL", "Monitor Normativo · nuevosBAires <alertas@nuevosbaires.com.ar>")
WEB_BASE_URL = os.environ.get("WEB_BASE_URL", "https://nuevosbaires.com.ar").rstrip("/")
RESEND_URL = "https://api.resend.com/emails"


def invite_accept_url(token: str) -> str:
    return f"{WEB_BASE_URL}/auth/invite?token={token}"


def render_invitation(
    workspace_name: str, role: str, accept_url: str, invited_by: str | None = None
) -> str:
    return invitacion(web_base_url=WEB_BASE_URL, workspace_name=workspace_name, role=role,
                      accept_url=accept_url, invited_by=invited_by)


async def send_invitation_email(
    *, to: str, workspace_name: str, role: str, token: str, invited_by: str | None = None
) -> dict:
    """Manda el email de invitación. No-op sin key; nunca levanta excepción."""
    if not RESEND_API_KEY:
        print(f"[emails] (sin RESEND_API_KEY) invitación a {to} para {workspace_name}")
        return {"skipped": True, "to": to}
    accept_url = invite_accept_url(token)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                json={
                    "from": ALERTS_FROM_EMAIL,
                    "to": [to],
                    "subject": f"Te invitaron a {workspace_name} en el Monitor Normativo",
                    "html": render_invitation(workspace_name, role, accept_url, invited_by),
                },
            )
            resp.raise_for_status()
            return {"sent": True, "to": to, "id": resp.json().get("id")}
    except Exception as exc:
        print(f"[emails] error enviando invitación a {to}: {exc!r}")
        return {"error": str(exc), "to": to}
