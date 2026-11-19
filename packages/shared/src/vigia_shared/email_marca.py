"""Marco HTML de los emails con la identidad nuevosBAires.

Lo usan las invitaciones (API), el digest de alertas y los reportes
programados (worker). Clientes de correo: solo estilos inline y tablas; el
logo va en PNG (muchos clientes bloquean SVG) servido por la web desde
`/brand/nuevosbaires-logo-blanco.png`.

Paleta: carbón #1D1D1B, lima #D3D93A, magenta #E62580, turquesa #4DB4B0,
lavanda #8F82BA; links y énfasis en magenta profundo #C21C6B (5,7:1 sobre
blanco). Las cuatro barras del isotipo van como franja bajo el encabezado.
"""
from __future__ import annotations

import html as _html

CARBON = "#1D1D1B"
GRIS = "#5C5C57"
BORDE = "#E4E4DF"
MAGENTA_PROFUNDO = "#C21C6B"
LIMA = "#D3D93A"
BARRAS = ("#D3D93A", "#E62580", "#4DB4B0", "#8F82BA")
FUENTE = "'Rethink Sans',Arial,Helvetica,sans-serif"
SITIO = "nuevosbaires.com.ar"
CONTACTO = "contacto@nuevosbaires.com.ar"


def esc(value) -> str:
    """Escapa texto de usuarios o terceros antes de interpolarlo en HTML."""
    return _html.escape(str(value)) if value is not None else ""


def boton(url: str, texto: str) -> str:
    """Botón principal: lima con texto carbón (11,1:1)."""
    return (
        f'<a href="{esc(url)}" style="display:inline-block;background:{LIMA};color:{CARBON};'
        f'font-family:{FUENTE};font-weight:700;font-size:14px;padding:12px 22px;border-radius:4px;'
        f'text-decoration:none">{esc(texto)}</a>'
    )


def marco(*, web_base_url: str, rotulo: str, titulo: str, subtitulo: str = "",
          cuerpo: str, motivo: str) -> str:
    """Email completo: encabezado carbón con logo, franja de barras, cuerpo y pie.

    `rotulo`, `titulo`, `subtitulo` y `motivo` son texto plano (se escapan);
    `cuerpo` es HTML ya armado por quien llama.
    """
    base = web_base_url.rstrip("/")
    franja = "".join(f'<td style="height:4px;background:{c};font-size:0;line-height:0">&nbsp;</td>' for c in BARRAS)
    sub = (
        f'<p style="margin:6px 0 0;font-size:14px;line-height:20px;color:rgba(255,255,255,.86)">{esc(subtitulo)}</p>'
        if subtitulo else ""
    )
    return (
        f'<div style="font-family:{FUENTE};background:#FFFFFF;max-width:640px;border:1px solid {BORDE};'
        f'border-radius:8px;overflow:hidden;color:{CARBON}">'
        f'<div style="background:{CARBON};padding:22px 24px;color:#FFFFFF">'
        f'<img src="{base}/brand/nuevosbaires-logo-blanco.png" alt="nuevosBAires" width="150" height="32" '
        f'style="display:block;border:0;height:32px;width:auto;margin:0 0 16px">'
        f'<p style="margin:0 0 6px;font-size:11px;font-weight:500;letter-spacing:.14em;color:rgba(255,255,255,.86)">{esc(rotulo)}</p>'
        f'<p style="margin:0;font-size:22px;line-height:28px;font-weight:700">{esc(titulo)}</p>{sub}</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse"><tr>{franja}</tr></table>'
        f'<div style="padding:22px 24px">{cuerpo}</div>'
        f'<div style="padding:12px 24px;border-top:1px solid {BORDE};font-size:11px;line-height:17px;color:{GRIS}">'
        f'Monitor Normativo · nuevosBAires · <a href="https://{SITIO}" style="color:{GRIS}">{SITIO}</a> · '
        f'<a href="mailto:{CONTACTO}" style="color:{GRIS}">{CONTACTO}</a><br>{esc(motivo)}</div></div>'
    )


def invitacion(*, web_base_url: str, workspace_name: str, role: str, accept_url: str,
               invited_by: str | None = None) -> str:
    """Email de invitación a un workspace (mismo texto en API y worker)."""
    quien = f" por <strong>{esc(invited_by)}</strong>" if invited_by else ""
    cuerpo = (
        f'<p style="margin:0 0 20px;font-size:15px;line-height:23px">Te invitaron{quien} a sumarte como '
        f'<strong>{esc(role)}</strong> al espacio <strong>{esc(workspace_name)}</strong> del Monitor Normativo, '
        f'el monitor de la normativa porteña: Boletín Oficial, Legislatura y Tribunal Superior.</p>'
        f'{boton(accept_url, "Aceptar invitación")}'
        f'<p style="margin:18px 0 0;font-size:12px;line-height:18px;color:{GRIS}">Si el botón no funciona, '
        f'abrí este link: <a href="{esc(accept_url)}" style="color:{MAGENTA_PROFUNDO}">{esc(accept_url)}</a></p>'
    )
    return marco(
        web_base_url=web_base_url, rotulo="MONITOR NORMATIVO · INVITACIÓN",
        titulo=f"Te invitaron a {workspace_name}", cuerpo=cuerpo,
        motivo="Recibís este email porque alguien te invitó a su espacio en el monitor.",
    )
