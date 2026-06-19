"""Envío de email. Dos backends, elegidos por entorno (sin tocar el código):

- **SMTP** (ej. Gmail): si hay ``SMTP_HOST`` + ``SMTP_USER`` + ``SMTP_PASSWORD``.
  Para Gmail: host ``smtp.gmail.com``, puerto 587, y una *Contraseña de
  aplicación* de 16 caracteres (NO la contraseña de la cuenta; requiere 2FA).
- **Resend** (HTTP API): si hay ``RESEND_API_KEY`` y no hay SMTP configurado.

Si no hay ninguno, es no-op limpio (loguea y sigue). Las credenciales viven
SOLO en el entorno — nunca en el repo.
"""
from __future__ import annotations

import html as _html
import os
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

import httpx


def _esc(value) -> str:
    """Escapa texto controlable por usuario/terceros antes de interpolarlo en HTML."""
    return _html.escape(str(value)) if value is not None else ""

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ALERTS_FROM_EMAIL = os.environ.get("ALERTS_FROM_EMAIL", "Vigía <alertas@openarg.org>")
WEB_BASE_URL = os.environ.get("WEB_BASE_URL", "https://vigia.openarg.org").rstrip("/")
RESEND_URL = "https://api.resend.com/emails"

# SMTP (ej. Gmail). Si SMTP_HOST está seteado, este backend tiene prioridad.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


def _send_smtp(*, to: str, subject: str, html: str) -> dict:
    """Envía via SMTP con STARTTLS (Gmail: smtp.gmail.com:587)."""
    msg = EmailMessage()
    msg["Subject"] = subject
    # Gmail reescribe el From al de la cuenta autenticada; respetamos el display
    # name de ALERTS_FROM_EMAIL pero la dirección efectiva es SMTP_USER.
    display_name, addr = parseaddr(ALERTS_FROM_EMAIL)
    msg["From"] = f"{display_name} <{SMTP_USER}>" if display_name else SMTP_USER
    msg["To"] = to
    msg.set_content("Tu cliente no soporta HTML. Abrí el monitor en " + WEB_BASE_URL)
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return {"sent": True, "to": to, "backend": "smtp"}
    except Exception as exc:  # pragma: no cover
        print(f"[notifications] error SMTP a {to}: {exc!r}")
        return {"error": str(exc), "to": to}


def send_email(*, to: str, subject: str, html: str) -> dict:
    """Envía un email por el backend disponible (SMTP > Resend > no-op)."""
    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        return _send_smtp(to=to, subject=subject, html=html)
    if not RESEND_API_KEY:
        print(f"[notifications] (sin backend de email) email a {to}: {subject}")
        return {"skipped": True, "to": to}
    try:
        resp = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": ALERTS_FROM_EMAIL, "to": [to], "subject": subject, "html": html},
            timeout=15.0,
        )
        resp.raise_for_status()
        return {"sent": True, "to": to, "id": resp.json().get("id"), "backend": "resend"}
    except Exception as exc:  # pragma: no cover
        print(f"[notifications] error enviando a {to}: {exc!r}")
        return {"error": str(exc), "to": to}


def render_digest(workspace_name: str, items: list[dict]) -> str:
    """HTML del digest de alertas, con link al detalle de cada norma."""
    rows = "".join(
        f'<tr><td style="padding:10px 0;border-bottom:1px solid #1f2937">'
        f'<p style="margin:0 0 2px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#74ACDF">'
        f'{_esc(i["keyword"])} · {_esc(i["tipo"])} {_esc(i.get("numero") or "")}</p>'
        f'<a href="{WEB_BASE_URL}/norma/{int(i["id"])}" '
        f'style="color:#E8ECF4;font-size:14px;font-weight:600;text-decoration:none">{_esc(i["titulo"])}</a>'
        f"</td></tr>"
        if i.get("id")
        else f'<tr><td style="padding:10px 0;border-bottom:1px solid #1f2937">'
        f'<p style="margin:0;color:#E8ECF4;font-size:14px"><strong>{_esc(i["keyword"])}</strong> — '
        f'{_esc(i["tipo"])} {_esc(i.get("numero") or "")}: {_esc(i["titulo"])}</p></td></tr>'
        for i in items
    )
    detectadas = (
        "Se detectó 1 coincidencia"
        if len(items) == 1
        else f"Se detectaron {len(items)} coincidencias"
    )
    return (
        f'<div style="font-family:Inter,system-ui,sans-serif;background:#06090F;color:#E8ECF4;'
        f'padding:32px 24px;border-radius:12px;max-width:600px">'
        f'<p style="margin:0 0 4px;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#636E85">'
        f"VIGÍA / ALERTAS</p>"
        f'<h2 style="margin:0 0 6px;font-size:20px;color:#E8ECF4">Nuevas normas para '
        f'<em style="color:#F6B40E;font-style:italic">{_esc(workspace_name)}</em></h2>'
        f'<p style="margin:0 0 18px;font-size:13px;color:#8892A8">'
        f"{detectadas} con tus alertas:</p>"
        f'<table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'<p style="margin:20px 0 0;font-size:12px"><a href="{WEB_BASE_URL}/alerts" '
        f'style="color:#74ACDF;text-decoration:none">Gestionar mis alertas →</a></p>'
        f'<p style="margin:14px 0 0;color:#636E85;font-size:11px">Inteligencia legislativa · Colossus Lab</p>'
        f"</div>"
    )


def render_invitation(
    workspace_name: str, role: str, accept_url: str, invited_by: str | None = None
) -> str:
    """HTML del email de invitación a un workspace."""
    inviter = f" por <strong>{_esc(invited_by)}</strong>" if invited_by else ""
    return (
        f'<div style="font-family:Inter,system-ui,sans-serif;background:#06090F;color:#E8ECF4;'
        f'padding:32px 24px;border-radius:12px;max-width:600px">'
        f'<p style="margin:0 0 4px;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#636E85">'
        f"VIGÍA / INVITACIÓN</p>"
        f'<h2 style="margin:0 0 10px;font-size:20px;color:#E8ECF4">Te invitaron a '
        f'<em style="color:#F6B40E;font-style:italic">{_esc(workspace_name)}</em></h2>'
        f'<p style="margin:0 0 22px;font-size:13px;color:#8892A8;line-height:1.6">'
        f"Fuiste invitado{inviter} a sumarte como <strong>{_esc(role)}</strong> al workspace "
        f"<strong>{_esc(workspace_name)}</strong> en Vigía, la plataforma de inteligencia "
        f"legislativa y regulatoria argentina.</p>"
        f'<a href="{accept_url}" style="display:inline-block;background:#74ACDF;color:#06090F;'
        f'font-weight:700;font-size:14px;padding:10px 22px;border-radius:999px;text-decoration:none">'
        f"Aceptar invitación</a>"
        f'<p style="margin:18px 0 0;font-size:11px;color:#636E85">Si el botón no funciona, '
        f'abrí este link: <a href="{accept_url}" style="color:#74ACDF">{accept_url}</a></p>'
        f'<p style="margin:14px 0 0;color:#636E85;font-size:11px">Inteligencia legislativa · Colossus Lab</p>'
        f"</div>"
    )
