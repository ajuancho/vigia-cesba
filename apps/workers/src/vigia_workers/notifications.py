"""Envío de email. Dos backends, elegidos por entorno (sin tocar el código):

- **SMTP** (ej. Gmail): si hay ``SMTP_HOST`` + ``SMTP_USER`` + ``SMTP_PASSWORD``.
  Para Gmail: host ``smtp.gmail.com``, puerto 587, y una *Contraseña de
  aplicación* de 16 caracteres (NO la contraseña de la cuenta; requiere 2FA).
- **Resend** (HTTP API): si hay ``RESEND_API_KEY`` y no hay SMTP configurado.

Si no hay ninguno, es no-op limpio (loguea y sigue). Las credenciales viven
SOLO en el entorno — nunca en el repo.
"""
from __future__ import annotations

import base64
import html as _html
import os
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

import httpx

from vigia_shared.email_marca import BORDE, GRIS, MAGENTA_PROFUNDO, boton, invitacion, marco


def _esc(value) -> str:
    """Escapa texto controlable por usuario/terceros antes de interpolarlo en HTML."""
    return _html.escape(str(value)) if value is not None else ""

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ALERTS_FROM_EMAIL = os.environ.get("ALERTS_FROM_EMAIL", "Monitor Normativo · nuevosBAires <alertas@nuevosbaires.com.ar>")
WEB_BASE_URL = os.environ.get("WEB_BASE_URL", "https://nuevosbaires.com.ar").rstrip("/")
RESEND_URL = "https://api.resend.com/emails"

# SMTP (ej. Gmail). Si SMTP_HOST está seteado, este backend tiene prioridad.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


# Adjunto: (nombre de archivo, bytes, media type "tipo/subtipo").
Adjunto = tuple[str, bytes, str]


def _send_smtp(*, to: str, subject: str, html: str, adjuntos: list[Adjunto] | None = None) -> dict:
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
    for nombre, data, mime in adjuntos or []:
        maintype, subtype = mime.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=nombre)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return {"sent": True, "to": to, "backend": "smtp"}
    except Exception as exc:  # pragma: no cover
        print(f"[notifications] error SMTP a {to}: {exc!r}")
        return {"error": str(exc), "to": to}


def send_email(*, to: str, subject: str, html: str, adjuntos: list[Adjunto] | None = None) -> dict:
    """Envía un email por el backend disponible (SMTP > Resend > no-op)."""
    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        return _send_smtp(to=to, subject=subject, html=html, adjuntos=adjuntos)
    if not RESEND_API_KEY:
        print(f"[notifications] (sin backend de email) email a {to}: {subject}")
        return {"skipped": True, "to": to}
    try:
        resp = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": ALERTS_FROM_EMAIL, "to": [to], "subject": subject, "html": html,
                **({"attachments": [
                    {"filename": nombre, "content": base64.b64encode(data).decode()}
                    for nombre, data, _ in adjuntos
                ]} if adjuntos else {}),
            },
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
        f'<tr><td style="padding:10px 0;border-top:1px solid {BORDE}">'
        f'<p style="margin:0 0 3px;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:{GRIS}">'
        f'{_esc(i["keyword"])} · {_esc(i["tipo"])} {_esc(i.get("numero") or "")}</p>'
        + (f'<a href="{WEB_BASE_URL}/norma/{int(i["id"])}" '
           f'style="color:{MAGENTA_PROFUNDO};font-size:14px;font-weight:600;text-decoration:none">{_esc(i["titulo"])}</a>'
           if i.get("id") else f'<span style="font-size:14px;font-weight:600">{_esc(i["titulo"])}</span>')
        + "</td></tr>"
        for i in items
    )
    detectadas = (
        "Se detectó 1 coincidencia"
        if len(items) == 1
        else f"Se detectaron {len(items)} coincidencias"
    )
    cuerpo = (
        f'<p style="margin:0 0 14px;font-size:14px;color:{GRIS}">{detectadas} con tus alertas:</p>'
        f'<table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'<p style="margin:22px 0 0">{boton(f"{WEB_BASE_URL}/alerts", "Gestionar mis alertas")}</p>'
    )
    return marco(
        web_base_url=WEB_BASE_URL, rotulo="MONITOR NORMATIVO · ALERTAS",
        titulo=f"Novedades para {workspace_name}", cuerpo=cuerpo,
        motivo="Recibís este email porque configuraste alertas en el monitor.",
    )


def render_invitation(
    workspace_name: str, role: str, accept_url: str, invited_by: str | None = None
) -> str:
    """HTML del email de invitación a un workspace."""
    return invitacion(web_base_url=WEB_BASE_URL, workspace_name=workspace_name, role=role,
                      accept_url=accept_url, invited_by=invited_by)
